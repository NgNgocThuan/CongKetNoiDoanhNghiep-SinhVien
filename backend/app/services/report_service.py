"""Nghiệp vụ: Báo cáo vi phạm. Người phụ trách: TV1."""
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import JobStatus, ReportStatus, ReportTargetType, UserStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import Company, Job, Report, Student, User
from app.schemas.common import PageParams
from app.schemas.reports import ReportCreate, ReportHandle
from app.services import email_service, notification_service
from app.utils.datetime_utils import utcnow
from app.utils.pagination import paginate


def create_report(db: Session, reporter: User, data: ReportCreate) -> Report:
    """Tạo báo cáo vi phạm mới (kiểm tra đối tượng tồn tại và chống spam duplicate)."""
    if data.target_type == ReportTargetType.JOB:
        target = db.get(Job, data.target_id)
    elif data.target_type == ReportTargetType.COMPANY:
        target = db.get(Company, data.target_id)
    elif data.target_type == ReportTargetType.STUDENT:
        target = db.get(Student, data.target_id)
    else:
        target = None

    if target is None:
        raise NotFoundError("Không tìm thấy đối tượng bị báo cáo")

    existing_pending = db.scalars(
        select(Report)
        .where(Report.reporter_id == reporter.id)
        .where(Report.target_type == data.target_type)
        .where(Report.target_id == data.target_id)
        .where(Report.status == ReportStatus.PENDING)
    ).first()
    if existing_pending is not None:
        raise ConflictError("Bạn đã gửi báo cáo cho đối tượng này và đang chờ xử lý")

    report = Report(
        reporter_id=reporter.id,
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session,
    params: PageParams,
    *,
    status: Optional[ReportStatus] = None,
    target_type: Optional[ReportTargetType] = None,
) -> dict:
    """Danh sách báo cáo vi phạm (dành cho admin)."""
    stmt = select(Report)

    if status:
        stmt = stmt.where(Report.status == status)
    if target_type:
        stmt = stmt.where(Report.target_type == target_type)

    stmt = stmt.order_by(Report.created_at.desc(), Report.id.desc())
    return paginate(db, stmt, params)


def get_report(db: Session, report_id: int) -> Report:
    """Chi tiết báo cáo vi phạm."""
    report = db.get(Report, report_id)
    if report is None:
        raise NotFoundError("Không tìm thấy báo cáo vi phạm")
    return report


def handle_report(
    db: Session,
    report_id: int,
    admin: User,
    data: ReportHandle,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Report:
    """Xử lý báo cáo vi phạm: giải quyết hoặc từ chối."""
    if data.status not in (ReportStatus.RESOLVED, ReportStatus.REJECTED):
        raise BadRequestError("Trạng thái xử lý phải là RESOLVED hoặc REJECTED")

    report = get_report(db, report_id)
    if report.status != ReportStatus.PENDING:
        raise ConflictError("Báo cáo này đã được xử lý trước đó")

    report.status = data.status
    report.handled_by = admin.id
    report.handled_at = utcnow()
    report.resolution_note = data.resolution_note

    locked_target_user: Optional[User] = None

    if data.status == ReportStatus.RESOLVED:
        # Tự động đóng tin tuyển dụng vi phạm
        if data.close_target_job and report.target_type == ReportTargetType.JOB:
            job = db.get(Job, report.target_id)
            if job is not None and job.status != JobStatus.CLOSED:
                job.status = JobStatus.CLOSED
                if data.resolution_note:
                    job.reject_reason = data.resolution_note

        # Tự động khóa tài khoản vi phạm
        if data.lock_target_user:
            target_user: Optional[User] = None
            if report.target_type == ReportTargetType.JOB:
                job = db.get(Job, report.target_id)
                if job is not None and job.company is not None:
                    target_user = job.company.user
            elif report.target_type == ReportTargetType.COMPANY:
                comp = db.get(Company, report.target_id)
                if comp is not None:
                    target_user = comp.user
            elif report.target_type == ReportTargetType.STUDENT:
                stud = db.get(Student, report.target_id)
                if stud is not None:
                    target_user = stud.user

            if (
                target_user is not None
                and target_user.id != admin.id
                and target_user.status != UserStatus.LOCKED
            ):
                target_user.status = UserStatus.LOCKED
                target_user.locked_reason = (
                    data.resolution_note or f"Khóa do vi phạm từ báo cáo #{report.id}"
                )
                notification_service.create_notification(
                    db,
                    user_id=target_user.id,
                    type="ACCOUNT_LOCKED",
                    title="Tài khoản đã bị tạm khóa do vi phạm",
                    content=target_user.locked_reason,
                    commit=False,
                )
                locked_target_user = target_user

    # Gửi thông báo cho người báo cáo
    notification_service.create_notification(
        db,
        user_id=report.reporter_id,
        type="REPORT_HANDLED",
        title="Báo cáo vi phạm đã được xử lý",
        content=f"Báo cáo #{report.id} đã được xử lý ({data.status.value}). Ghi chú: {data.resolution_note or 'Không có'}",
        ref_type="REPORT",
        ref_id=report.id,
        commit=False,
    )
    db.commit()
    db.refresh(report)

    if background_tasks is not None:
        if locked_target_user is not None and locked_target_user.email:
            lock_subject, lock_body_html = email_service.render_email_template(
                "ACCOUNT_LOCKED", {"reason": locked_target_user.locked_reason or ""}
            )
            email_service.queue_email(
                db,
                background_tasks,
                to_email=locked_target_user.email,
                subject=lock_subject,
                body_html=lock_body_html,
                type="ACCOUNT_LOCKED",
                user_id=locked_target_user.id,
            )

        reporter = db.get(User, report.reporter_id)
        if reporter is not None:
            subject, body_html = email_service.render_email_template(
                "REPORT_HANDLED",
                {
                    "report_id": report.id,
                    "status": data.status.value,
                    "resolution_note": data.resolution_note or "",
                },
            )
            email_service.queue_email(
                db,
                background_tasks,
                to_email=reporter.email,
                subject=subject,
                body_html=body_html,
                type="REPORT_HANDLED",
                user_id=reporter.id,
                ref_type="REPORT",
                ref_id=report.id,
            )

    return report
