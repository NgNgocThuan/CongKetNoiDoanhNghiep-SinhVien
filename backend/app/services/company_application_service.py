"""Nghiệp vụ: Quản lý ứng viên (Kanban). Người phụ trách: Khôi."""

from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.enums import ApplicationStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import (
    Application,
    ApplicationStatusLog,
    Company,
    Job,
    Student,
    StudentExperience,
    StudentProfile,
    StudentSkill,
)
from app.schemas.common import PageParams
from app.services.email_service import queue_email
from app.services.notification_service import create_notification
from app.utils.datetime_utils import utcnow
from app.utils.pagination import paginate

# Quy tắc chuyển trạng thái hợp lệ
_VALID_TRANSITIONS = {
    ApplicationStatus.APPLIED: {
        ApplicationStatus.SCREENING,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.SCREENING: {
        ApplicationStatus.SHORTLISTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.SHORTLISTED: {
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.INTERVIEW: {
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.OFFER: {
        ApplicationStatus.HIRED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
}


def _get_owned_application(db: Session, company: Company, application_id: int) -> Application:
    stmt = (
        select(Application)
        .join(Application.job)
        .where(Application.id == application_id, Job.company_id == company.id)
        .options(
            selectinload(Application.job),
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.profile),
            selectinload(Application.student).selectinload(Student.experiences),
            selectinload(Application.student)
            .selectinload(Student.skills)
            .selectinload(StudentSkill.skill),
            selectinload(Application.cv),
            selectinload(Application.status_logs),
        )
    )
    app = db.scalars(stmt).first()
    if not app:
        raise NotFoundError("Không tìm thấy đơn ứng tuyển thuộc tin của doanh nghiệp")
    return app


def list_applications(
    db: Session,
    company: Company,
    job_id: int,
    params: PageParams,
    status: Optional[ApplicationStatus] = None,
    major_id: Optional[int] = None,
    min_gpa: Optional[float] = None,
    skill_id: Optional[int] = None,
    min_experience_months: Optional[int] = None,
) -> dict:
    """Danh sách đơn theo job_id; lọc ngành, GPA, kỹ năng, kinh nghiệm; hỗ trợ Kanban."""
    job = db.get(Job, job_id)
    if not job or job.company_id != company.id:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")

    stmt = (
        select(Application)
        .join(Application.student)
        .where(Application.job_id == job_id)
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.major),
            selectinload(Application.student).selectinload(Student.profile),
            selectinload(Application.student).selectinload(Student.experiences),
            selectinload(Application.student)
            .selectinload(Student.skills)
            .selectinload(StudentSkill.skill),
            selectinload(Application.cv),
            selectinload(Application.status_logs),
        )
    )

    if status is not None:
        stmt = stmt.where(Application.current_status == status)
    if major_id is not None:
        stmt = stmt.where(Student.major_id == major_id)
    if min_gpa is not None:
        stmt = stmt.where(
            Student.gpa >= min_gpa, Student.profile.has(StudentProfile.show_gpa.is_(True))
        )
    if skill_id is not None:
        stmt = stmt.where(
            Application.student_id.in_(
                select(StudentSkill.student_id).where(StudentSkill.skill_id == skill_id)
            )
        )

    if min_experience_months is not None:
        end = func.coalesce(StudentExperience.end_date, utcnow().date())
        months = (
            (extract("year", end) - extract("year", StudentExperience.start_date)) * 12
            + extract("month", end)
            - extract("month", StudentExperience.start_date)
        )
        experience = (
            select(func.coalesce(func.sum(case((months > 0, months), else_=0)), 0))
            .where(
                StudentExperience.student_id == Student.id,
                StudentExperience.start_date.is_not(None),
            )
            .correlate(Student)
            .scalar_subquery()
        )
        stmt = stmt.where(experience >= min_experience_months)
    stmt = stmt.order_by(Application.applied_at.desc(), Application.id.desc())
    result = paginate(db, stmt, params)
    result["items"] = [application_payload(app) for app in result["items"]]
    return result


def application_payload(app: Application) -> dict:
    student = app.student
    profile = student.profile
    show_contact = profile is not None and profile.show_contact
    today = utcnow().date()
    months = sum(
        max(
            0,
            ((exp.end_date or today).year - exp.start_date.year) * 12
            + (exp.end_date or today).month
            - exp.start_date.month,
        )
        for exp in student.experiences
        if exp.start_date
    )
    return {
        "id": app.id,
        "job_id": app.job_id,
        "student_id": app.student_id,
        "cv_id": app.cv_id,
        "current_status": app.current_status,
        "cover_letter": app.cover_letter,
        "applied_at": app.applied_at,
        "updated_at": app.updated_at,
        "contact_email": (profile.contact_email or student.user.email) if show_contact else None,
        "contact_phone": (profile.contact_phone or student.phone) if show_contact else None,
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "gpa": student.gpa if profile is not None and profile.show_gpa else None,
            "experience_months": months,
            "skills": [item.skill.name for item in student.skills],
        },
        "status_logs": app.status_logs,
        "cv_snapshot_url": app.cv_snapshot_url,
        "cv_download_url": f"{settings.API_V1_PREFIX}/company/applications/{app.id}/cv",
    }


def get_application(db: Session, company: Company, application_id: int) -> dict:
    return application_payload(_get_owned_application(db, company, application_id))


def log_status_change(
    db: Session,
    background_tasks: BackgroundTasks,
    company: Company,
    application_id: int,
    new_status: ApplicationStatus,
    note: Optional[str] = None,
) -> dict:
    app = _get_owned_application(db, company, application_id)
    old_status = app.current_status

    if old_status in (
        ApplicationStatus.HIRED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ):
        raise ConflictError(
            "Đơn đã ở trạng thái kết thúc, không thể thay đổi", code="APPLICATION_CLOSED"
        )

    if new_status != old_status:
        allowed = _VALID_TRANSITIONS.get(old_status, set())
        if new_status != ApplicationStatus.REJECTED and new_status not in allowed:
            raise BadRequestError(
                f"Không thể chuyển trạng thái từ {old_status.value} sang {new_status.value}"
            )

    app.current_status = new_status

    status_log = ApplicationStatusLog(
        application_id=app.id,
        old_status=old_status.value if isinstance(old_status, ApplicationStatus) else old_status,
        new_status=new_status.value if isinstance(new_status, ApplicationStatus) else new_status,
        changed_by=company.user_id,
        note=note,
    )
    db.add(status_log)
    db.commit()
    db.refresh(app)

    student_user = app.student.user
    if student_user:
        title = "Cập nhật trạng thái đơn ứng tuyển"
        content = f"Đơn ứng tuyển vào vị trí '{app.job.title}' đã chuyển sang trạng thái: {new_status.value}."
        if note:
            content += f" Ghi chú: {note}"

        create_notification(
            db,
            user_id=student_user.id,
            type="APPLICATION_STATUS",
            title=title,
            content=content,
            ref_type="APPLICATION",
            ref_id=app.id,
        )

        email_body = f"<p>Xin chào {app.student.full_name},</p><p>{content}</p>"
        queue_email(
            db,
            background_tasks,
            to_email=student_user.email,
            subject="Cập nhật trạng thái đơn ứng tuyển",
            body_html=email_body,
            type="STATUS_CHANGED",
            user_id=student_user.id,
            ref_type="APPLICATION",
            ref_id=app.id,
        )

    return application_payload(app)


def get_history(db: Session, company: Company, application_id: int) -> list[ApplicationStatusLog]:
    app = _get_owned_application(db, company, application_id)
    return app.status_logs
