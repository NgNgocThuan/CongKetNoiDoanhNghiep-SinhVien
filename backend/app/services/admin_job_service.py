"""Nghiệp vụ: Nhà trường: kiểm duyệt tin tuyển dụng. Người phụ trách: TV1."""
import logging
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import SessionLocal
from app.core.enums import JobStatus, UserStatus, VerificationStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import Company, Job, User
from app.schemas.admin_jobs import JobRejectRequest
from app.schemas.common import PageParams
from app.services import email_service, notification_service
from app.utils.datetime_utils import utcnow
from app.utils.pagination import paginate

logger = logging.getLogger(__name__)


def _safe_parse_job_task(job_id: int, db_session: Optional[Session] = None) -> None:
    """Tác vụ chạy nền phân tích tin tuyển dụng qua AI (bọc try-except không làm sập tiến trình)."""
    session_to_close: Optional[Session] = None

    try:
        # ƯU TIÊN KIỂM TRA db_session trước để tránh timeout TCP tới MariaDB trong test
        if db_session is not None:
            session_to_close = Session(bind=db_session.get_bind(), autoflush=False, expire_on_commit=False)
            db = session_to_close
        else:
            session_to_close = SessionLocal()
            db = session_to_close

        job = db.get(Job, job_id)
        if job is None:
            return

        try:
            from app.ai.job_parser import parse_job

            parse_job(db, job)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Phân tích AI cho tin tuyển dụng #%s chưa hoàn thành hoặc đang phát triển: %s",
                job_id,
                exc,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lỗi trong tác vụ phân tích tin tuyển dụng #%s: %s", job_id, exc)
    finally:
        if session_to_close is not None:
            session_to_close.close()


def list_jobs(
    db: Session,
    params: PageParams,
    *,
    status: Optional[JobStatus] = JobStatus.PENDING_APPROVAL,
    company_id: Optional[int] = None,
    term_id: Optional[int] = None,
    q: Optional[str] = None,
) -> dict:
    """Danh sách tin tuyển dụng cho admin kiểm duyệt."""
    stmt = select(Job)

    if status is not None:
        stmt = stmt.where(Job.status == status)
    if company_id is not None:
        stmt = stmt.where(Job.company_id == company_id)
    if term_id is not None:
        stmt = stmt.where(Job.term_id == term_id)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Job.title).like(like),
                func.lower(Job.position).like(like),
            )
        )

    stmt = stmt.order_by(Job.created_at.desc(), Job.id.desc())
    return paginate(db, stmt, params)


def get_job(db: Session, job_id: int) -> Job:
    """Lấy chi tiết tin tuyển dụng."""
    stmt = (
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.company).selectinload(Company.user))
    )
    job = db.scalars(stmt).first()
    if job is None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    return job


def approve_job(
    db: Session,
    job_id: int,
    admin: User,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Job:
    """Duyệt tin tuyển dụng: đổi status=APPROVED, kích hoạt parse_job chạy nền."""
    job = get_job(db, job_id)

    if job.status == JobStatus.APPROVED:
        raise ConflictError("Tin tuyển dụng đã được phê duyệt trước đó")
    if job.status not in (JobStatus.PENDING_APPROVAL, JobStatus.REJECTED):
        raise BadRequestError("Chỉ có thể phê duyệt tin đang chờ duyệt")

    # [P1] Khóa chặt State Machine: kiểm tra trạng thái doanh nghiệp sở hữu tin
    if job.company is None or job.company.verification_status != VerificationStatus.APPROVED:
        raise BadRequestError("Doanh nghiệp sở hữu tin tuyển dụng chưa được phê duyệt")
    if job.company.user is not None and job.company.user.status != UserStatus.ACTIVE:
        raise BadRequestError("Tài khoản doanh nghiệp đang bị khóa hoặc chưa hoạt động")

    job.status = JobStatus.APPROVED
    job.approved_by = admin.id
    job.approved_at = utcnow()
    job.reject_reason = None

    if job.company is not None and job.company.user is not None:
        notification_service.create_notification(
            db,
            user_id=job.company.user_id,
            type="JOB_APPROVED",
            title=f"Tin tuyển dụng '{job.title}' đã được duyệt",
            content="Tin tuyển dụng của bạn đã được nhà trường kiểm duyệt và đang hiển thị công khai cho sinh viên.",
            ref_type="JOB",
            ref_id=job.id,
            commit=False,
        )

    db.commit()
    db.refresh(job)

    if background_tasks is not None:
        if job.company is not None and job.company.user is not None:
            subject, body_html = email_service.render_email_template(
                "JOB_APPROVED",
                {"job_title": job.title, "company_name": job.company.name},
            )
            email_service.queue_email(
                db,
                background_tasks,
                to_email=job.company.user.email,
                subject=subject,
                body_html=body_html,
                type="JOB_APPROVED",
                user_id=job.company.user_id,
                ref_type="JOB",
                ref_id=job.id,
            )
        background_tasks.add_task(_safe_parse_job_task, job.id, db)
    else:
        _safe_parse_job_task(job.id, db)

    return job


def reject_job(
    db: Session,
    job_id: int,
    admin: User,
    data: JobRejectRequest,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Job:
    """Từ chối duyệt tin tuyển dụng (bắt buộc nhập lý do)."""
    job = get_job(db, job_id)

    # [P1] Khóa chặt State Machine kiểm tra trạng thái tin
    if job.status == JobStatus.REJECTED:
        raise ConflictError("Tin tuyển dụng đã bị từ chối trước đó")
    if job.status != JobStatus.PENDING_APPROVAL:
        raise BadRequestError("Chỉ có thể từ chối tin đang ở trạng thái chờ duyệt")

    job.status = JobStatus.REJECTED
    job.approved_by = admin.id
    job.approved_at = utcnow()
    job.reject_reason = data.reject_reason

    if job.company is not None and job.company.user is not None:
        notification_service.create_notification(
            db,
            user_id=job.company.user_id,
            type="JOB_REJECTED",
            title=f"Tin tuyển dụng '{job.title}' chưa được duyệt",
            content=f"Lý do: {data.reject_reason}",
            ref_type="JOB",
            ref_id=job.id,
            commit=False,
        )

    db.commit()
    db.refresh(job)

    if background_tasks is not None and job.company is not None and job.company.user is not None:
        subject, body_html = email_service.render_email_template(
            "JOB_REJECTED",
            {"job_title": job.title, "reject_reason": data.reject_reason},
        )
        email_service.queue_email(
            db,
            background_tasks,
            to_email=job.company.user.email,
            subject=subject,
            body_html=body_html,
            type="JOB_REJECTED",
            user_id=job.company.user_id,
            ref_type="JOB",
            ref_id=job.id,
        )

    return job


def close_job(
    db: Session,
    job_id: int,
    admin: User,
    *,
    reason: Optional[str] = None,
) -> Job:
    """Đóng tin tuyển dụng vi phạm."""
    job = get_job(db, job_id)

    if job.status == JobStatus.CLOSED:
        raise ConflictError("Tin tuyển dụng đã bị đóng trước đó")

    job.status = JobStatus.CLOSED
    if reason:
        job.reject_reason = reason

    if job.company is not None and job.company.user is not None:
        notification_service.create_notification(
            db,
            user_id=job.company.user_id,
            type="JOB_CLOSED",
            title=f"Tin tuyển dụng '{job.title}' đã bị đóng",
            content=reason or "Quản trị viên đã đóng tin tuyển dụng này.",
            ref_type="JOB",
            ref_id=job.id,
            commit=False,
        )

    db.commit()
    db.refresh(job)
    return job
