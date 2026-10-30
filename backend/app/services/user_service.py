"""Nghiệp vụ: Quản lý tài khoản (admin). Người phụ trách: TV1."""
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import UserRole, UserStatus, VerificationStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import Admin, Faculty, User
from app.schemas.common import PageParams
from app.schemas.users import AdminCreate, LockUserRequest
from app.services import email_service, notification_service
from app.utils.pagination import paginate


def list_users(
    db: Session,
    params: PageParams,
    *,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    q: Optional[str] = None,
) -> dict:
    """Danh sách người dùng có phân trang và bộ lọc."""
    stmt = select(User).options(selectinload(User.admin))

    if role:
        stmt = stmt.where(User.role == role)
    if status:
        stmt = stmt.where(User.status == status)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like)))

    stmt = stmt.order_by(User.created_at.desc(), User.id.desc())
    return paginate(db, stmt, params)


def get_user(db: Session, user_id: int) -> User:
    """Chi tiết tài khoản người dùng."""
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.admin), selectinload(User.company), selectinload(User.student))
    )
    user = db.scalars(stmt).first()
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    return user


def lock_user(
    db: Session,
    user_id: int,
    data: LockUserRequest,
    *,
    current_admin: Optional[User] = None,
    background_tasks: Optional[BackgroundTasks] = None,
) -> User:
    """Khóa tài khoản và ghi nhận lý do khóa."""
    user = get_user(db, user_id)

    if current_admin is not None and current_admin.id == user.id:
        raise BadRequestError("Không thể tự khóa tài khoản của chính mình")

    if user.status == UserStatus.LOCKED:
        raise ConflictError("Tài khoản đã bị khóa trước đó")

    user.status = UserStatus.LOCKED
    user.locked_reason = data.reason

    notification_service.create_notification(
        db,
        user_id=user.id,
        type="ACCOUNT_LOCKED",
        title="Tài khoản đã bị tạm khóa",
        content=f"Tài khoản của bạn đã bị khóa với lý do: {data.reason}",
        commit=False,
    )
    db.commit()
    db.refresh(user)

    if background_tasks is not None:
        subject, body_html = email_service.render_email_template(
            "ACCOUNT_LOCKED",
            {"reason": data.reason},
        )
        email_service.queue_email(
            db,
            background_tasks,
            to_email=user.email,
            subject=subject,
            body_html=body_html,
            type="ACCOUNT_LOCKED",
            user_id=user.id,
        )

    return user


def unlock_user(
    db: Session,
    user_id: int,
    *,
    background_tasks: Optional[BackgroundTasks] = None,
) -> User:
    """Mở khóa tài khoản về trạng thái hợp lệ tương ứng."""
    user = get_user(db, user_id)

    if user.status != UserStatus.LOCKED:
        raise BadRequestError("Tài khoản không ở trạng thái bị khóa")

    # Khôi phục trạng thái chuẩn xác
    if user.password_hash is None:
        user.status = UserStatus.PENDING_ACTIVATION
    elif (
        user.role == UserRole.COMPANY
        and (user.company is None or user.company.verification_status != VerificationStatus.APPROVED)
    ):
        user.status = UserStatus.PENDING_APPROVAL
    else:
        user.status = UserStatus.ACTIVE

    user.locked_reason = None

    notification_service.create_notification(
        db,
        user_id=user.id,
        type="ACCOUNT_UNLOCKED",
        title="Tài khoản đã được mở khóa",
        content="Quản trị viên đã mở khóa tài khoản của bạn.",
        commit=False,
    )
    db.commit()
    db.refresh(user)

    if background_tasks is not None:
        subject, body_html = email_service.render_email_template("ACCOUNT_UNLOCKED")
        email_service.queue_email(
            db,
            background_tasks,
            to_email=user.email,
            subject=subject,
            body_html=body_html,
            type="ACCOUNT_UNLOCKED",
            user_id=user.id,
        )

    return user


def create_admin(db: Session, data: AdminCreate) -> User:
    """Tạo tài khoản quản trị viên mới (chỉ Admin thực hiện)."""
    normalized_email = data.email.strip().lower()
    existing_user = db.scalars(
        select(User).where(func.lower(User.email) == normalized_email)
    ).first()
    if existing_user is not None:
        raise ConflictError("Email đã được sử dụng")

    if data.faculty_id is not None:
        faculty = db.get(Faculty, data.faculty_id)
        if faculty is None or not faculty.is_active:
            raise NotFoundError("Không tìm thấy khoa")

    user = User(
        email=normalized_email,
        password_hash=hash_password(data.password),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()

    admin = Admin(
        user_id=user.id,
        full_name=data.full_name.strip(),
        faculty_id=data.faculty_id,
        position=data.position.strip() if data.position else None,
        phone=data.phone.strip() if data.phone else None,
    )
    db.add(admin)
    db.commit()
    db.refresh(user)

    return user
