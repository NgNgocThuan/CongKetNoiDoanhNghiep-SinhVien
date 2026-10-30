"""Nghiệp vụ: Nhà trường: kiểm duyệt doanh nghiệp. Người phụ trách: TV1."""
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import UserStatus, VerificationStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Company, User
from app.schemas.admin_companies import CompanyRejectRequest
from app.schemas.common import PageParams
from app.services import email_service, notification_service
from app.utils.datetime_utils import utcnow
from app.utils.pagination import paginate


def list_companies(
    db: Session,
    params: PageParams,
    *,
    verification_status: Optional[VerificationStatus] = None,
    q: Optional[str] = None,
) -> dict:
    """Danh sách doanh nghiệp dành cho admin xét duyệt."""
    stmt = select(Company)

    if verification_status:
        stmt = stmt.where(Company.verification_status == verification_status)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Company.name).like(like),
                func.lower(Company.tax_code).like(like),
            )
        )

    stmt = stmt.order_by(Company.created_at.desc(), Company.id.desc())
    return paginate(db, stmt, params)


def get_company_detail(db: Session, company_id: int) -> Company:
    """Chi tiết doanh nghiệp kèm danh sách giấy tờ xác thực."""
    stmt = (
        select(Company)
        .where(Company.id == company_id)
        .options(selectinload(Company.documents), selectinload(Company.user))
    )
    company = db.scalars(stmt).first()
    if company is None:
        raise NotFoundError("Không tìm thấy doanh nghiệp")
    return company


def approve_company(
    db: Session,
    company_id: int,
    admin: User,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Company:
    """Phê duyệt doanh nghiệp: kích hoạt tài khoản user, gửi thông báo + email."""
    company = get_company_detail(db, company_id)

    if company.user is not None and company.user.status == UserStatus.LOCKED:
        raise ConflictError("Tài khoản doanh nghiệp đang bị khóa, không thể phê duyệt")

    if company.verification_status == VerificationStatus.APPROVED:
        raise ConflictError("Doanh nghiệp đã được phê duyệt trước đó")

    company.verification_status = VerificationStatus.APPROVED
    company.verified_by = admin.id
    company.verified_at = utcnow()
    company.reject_reason = None

    if company.user is not None:
        company.user.status = UserStatus.ACTIVE

    notification_service.create_notification(
        db,
        user_id=company.user_id,
        type="COMPANY_APPROVED",
        title="Hồ sơ doanh nghiệp đã được phê duyệt",
        content="Chúc mừng! Hồ sơ doanh nghiệp của bạn đã được nhà trường phê duyệt thành công. Bạn đã có thể đăng tin tuyển dụng.",
        commit=False,
    )
    db.commit()
    db.refresh(company)

    if background_tasks is not None and company.user is not None:
        subject, body_html = email_service.render_email_template(
            "COMPANY_APPROVED",
            {"company_name": company.name},
        )
        email_service.queue_email(
            db,
            background_tasks,
            to_email=company.user.email,
            subject=subject,
            body_html=body_html,
            type="COMPANY_APPROVED",
            user_id=company.user_id,
        )

    return company


def reject_company(
    db: Session,
    company_id: int,
    admin: User,
    data: CompanyRejectRequest,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Company:
    """Từ chối hồ sơ doanh nghiệp (bắt buộc nhập lý do)."""
    company = get_company_detail(db, company_id)

    if company.user is not None and company.user.status == UserStatus.LOCKED:
        raise ConflictError("Tài khoản doanh nghiệp đang bị khóa")

    if company.verification_status == VerificationStatus.REJECTED:
        raise ConflictError("Doanh nghiệp đã bị từ chối trước đó")

    if company.verification_status == VerificationStatus.APPROVED:
        raise ConflictError("Không thể từ chối doanh nghiệp đã được phê duyệt")

    company.verification_status = VerificationStatus.REJECTED
    company.verified_by = admin.id
    company.verified_at = utcnow()
    company.reject_reason = data.reject_reason

    if company.user is not None and company.user.status != UserStatus.LOCKED:
        company.user.status = UserStatus.PENDING_APPROVAL

    notification_service.create_notification(
        db,
        user_id=company.user_id,
        type="COMPANY_REJECTED",
        title="Hồ sơ doanh nghiệp chưa được duyệt",
        content=f"Hồ sơ doanh nghiệp của bạn chưa được duyệt. Lý do: {data.reject_reason}",
        commit=False,
    )
    db.commit()
    db.refresh(company)

    if background_tasks is not None and company.user is not None:
        subject, body_html = email_service.render_email_template(
            "COMPANY_REJECTED",
            {"company_name": company.name, "reject_reason": data.reject_reason},
        )
        email_service.queue_email(
            db,
            background_tasks,
            to_email=company.user.email,
            subject=subject,
            body_html=body_html,
            type="COMPANY_REJECTED",
            user_id=company.user_id,
        )

    return company
