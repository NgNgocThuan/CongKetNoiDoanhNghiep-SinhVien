"""Application submission and student-side tracking business rules."""
import html
import json
import shutil
import uuid
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.core.enums import ApplicationStatus, CVType, InvitationStatus, JobStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import CV, Application, ApplicationStatusLog, Invitation, Job, Student, User
from app.schemas.applications import ApplicationCreate
from app.schemas.common import PageParams
from app.services import email_service, internship_service, notification_service
from app.utils.datetime_utils import today, utcnow
from app.utils.file_storage import absolute_path
from app.utils.pagination import paginate


def _status_value(status: ApplicationStatus | str) -> ApplicationStatus:
    try:
        return status if isinstance(status, ApplicationStatus) else ApplicationStatus(status)
    except ValueError as exc:
        raise BadRequestError("Trạng thái đơn ứng tuyển không hợp lệ") from exc


def _changed_by_id(changed_by: User | int | None) -> int | None:
    return changed_by.id if isinstance(changed_by, User) else changed_by


def log_status_change(
    db: Session,
    application: Application,
    new_status: ApplicationStatus | str,
    changed_by: User | int | None,
    note: str | None = None,
) -> ApplicationStatusLog:
    """Change current status and append its audit log without committing.

    The caller owns the surrounding transaction. TV4 uses this function for Kanban changes.
    """
    status = _status_value(new_status)
    is_new = application.id is None
    old_status = None if is_new else application.current_status.value
    if is_new:
        db.flush()
    application.current_status = status
    log = ApplicationStatusLog(
        application=application,
        old_status=old_status,
        new_status=status.value,
        changed_by=_changed_by_id(changed_by),
        note=note,
    )
    db.add(log)
    db.flush()
    return log


def _snapshot_cv(cv: CV) -> str:
    relative_dir = Path("applications") / "cv-snapshots" / str(cv.student_id)
    target_dir = Path(settings.UPLOAD_DIR) / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex

    if cv.type == CVType.UPLOADED:
        if not cv.file_url:
            raise NotFoundError("File CV không còn tồn tại")
        source = absolute_path(cv.file_url)
        if not source.is_file():
            raise NotFoundError("File CV không còn tồn tại")
        target = target_dir / f"{token}{source.suffix.lower()}"
        shutil.copy2(source, target)
    else:
        target = target_dir / f"{token}.json"
        target.write_text(
            json.dumps(cv.content_json or {}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return (relative_dir / target.name).as_posix()


def _get_invitation(
    db: Session, invitation_id: int, student: Student, job: Job
) -> Invitation:
    invitation = db.get(Invitation, invitation_id)
    if (
        invitation is None
        or invitation.student_id != student.id
        or invitation.job_id != job.id
        or invitation.company_id != job.company_id
    ):
        raise NotFoundError("Không tìm thấy lời mời ứng tuyển phù hợp")
    if invitation.status != InvitationStatus.PENDING:
        raise ConflictError("Lời mời đã được xử lý", code="INVITATION_PROCESSED")
    return invitation


def apply(
    db: Session,
    background_tasks: BackgroundTasks,
    student: Student,
    data: ApplicationCreate,
) -> Application:
    job = db.scalar(
        select(Job)
        .where(Job.id == data.job_id)
        .options(joinedload(Job.company))
    )
    if job is None or job.status != JobStatus.APPROVED or job.deadline < today():
        raise BadRequestError("Tin tuyển dụng không còn nhận ứng tuyển", code="JOB_NOT_OPEN")

    cv = db.get(CV, data.cv_id)
    if cv is None or cv.student_id != student.id or cv.deleted_at is not None:
        raise NotFoundError("Không tìm thấy CV hợp lệ")

    if job.term_id is not None and not internship_service.is_student_in_term(
        db, student.id, job.term_id
    ):
        raise BadRequestError(
            "Bạn không thuộc đợt thực tập của tin tuyển dụng này",
            code="NOT_IN_INTERNSHIP_TERM",
        )

    duplicate = db.scalar(
        select(Application.id).where(
            Application.student_id == student.id, Application.job_id == job.id
        )
    )
    if duplicate is not None:
        raise ConflictError("Bạn đã ứng tuyển tin này", code="DUPLICATE_APPLICATION")

    invitation = (
        _get_invitation(db, data.invitation_id, student, job)
        if data.invitation_id is not None
        else None
    )
    snapshot_url = _snapshot_cv(cv)
    application = Application(
        student_id=student.id,
        job_id=job.id,
        cv_id=cv.id,
        cv_snapshot_url=snapshot_url,
        cover_letter=data.cover_letter,
        invitation_id=invitation.id if invitation else None,
        current_status=ApplicationStatus.APPLIED,
    )
    db.add(application)
    log_status_change(db, application, ApplicationStatus.APPLIED, student.user_id)

    if invitation is not None:
        invitation.status = InvitationStatus.ACCEPTED
        invitation.responded_at = utcnow()

    notification_service.create_notification(
        db,
        user_id=job.company.user_id,
        type="NEW_APPLICATION",
        title="Có đơn ứng tuyển mới",
        content=f"{student.full_name} đã ứng tuyển vị trí {job.title}",
        ref_type="APPLICATION",
        ref_id=application.id,
        commit=False,
    )
    db.commit()
    db.refresh(application)

    email_service.queue_email(
        db,
        background_tasks,
        to_email=student.user.email,
        subject="Đơn ứng tuyển đã được ghi nhận",
        body_html=(
            f"<p>Xin chào {html.escape(student.full_name)},</p>"
            f"<p>Đơn ứng tuyển vị trí <strong>{html.escape(job.title)}</strong> "
            "đã được ghi nhận.</p>"
        ),
        type="APPLY_SUCCESS",
        user_id=student.user_id,
        ref_type="APPLICATION",
        ref_id=application.id,
    )
    return application


def _application_options():
    return (
        joinedload(Application.job).joinedload(Job.company),
        joinedload(Application.cv),
        selectinload(Application.status_logs),
    )


def list_my_applications(
    db: Session,
    student: Student,
    params: PageParams,
    *,
    status: ApplicationStatus | None = None,
) -> dict:
    stmt = select(Application).where(Application.student_id == student.id)
    if status is not None:
        stmt = stmt.where(Application.current_status == status)
    stmt = stmt.options(*_application_options()).order_by(
        Application.applied_at.desc(), Application.id.desc()
    )
    return paginate(db, stmt, params)


def get_my_application(db: Session, student: Student, application_id: int) -> Application:
    application = db.scalar(
        select(Application)
        .where(Application.id == application_id, Application.student_id == student.id)
        .options(*_application_options())
    )
    if application is None:
        raise NotFoundError("Không tìm thấy đơn ứng tuyển")
    application.status_logs.sort(key=lambda item: (item.changed_at, item.id))
    return application


def withdraw(db: Session, student: Student, application_id: int) -> Application:
    application = get_my_application(db, student, application_id)
    blocked = {
        ApplicationStatus.OFFER,
        ApplicationStatus.HIRED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    }
    if application.current_status in blocked:
        raise ConflictError("Không thể rút đơn ở trạng thái hiện tại", code="CANNOT_WITHDRAW")
    log_status_change(
        db,
        application,
        ApplicationStatus.WITHDRAWN,
        student.user_id,
        "Sinh viên chủ động rút đơn",
    )
    notification_service.create_notification(
        db,
        user_id=application.job.company.user_id,
        type="APPLICATION_WITHDRAWN",
        title="Sinh viên đã rút đơn",
        content=f"{student.full_name} đã rút đơn ứng tuyển vị trí {application.job.title}",
        ref_type="APPLICATION",
        ref_id=application.id,
        commit=False,
    )
    db.commit()
    return get_my_application(db, student, application.id)
