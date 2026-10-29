"""Nghiệp vụ: Xác thực & phiên đăng nhập. Người phụ trách: TV1."""
import time
from datetime import timedelta
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.enums import UserRole, UserStatus, VerificationStatus
from app.core.exceptions import (
    AppException,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.security import (
    clear_revoked_tokens,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
    hash_password,
    hash_token,
    revoke_token,
    verify_password,
)
from app.models import Company, Industry, PasswordResetToken, User
from app.schemas.auth import (
    ActivateAccountRequest,
    ChangePasswordRequest,
    RegisterCompanyRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.services import email_service
from app.utils.datetime_utils import utcnow

# Khởi tạo hằng số băm mật khẩu giả lập để chống Timing Attack
_DUMMY_PASSWORD_HASH = hash_password("DummyTimingProtection@2026")

# Bộ lưu trữ in-memory chống brute-force đăng nhập: email -> list[timestamp]
_failed_login_attempts: dict[str, list[float]] = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 60.0

# Bộ lưu trữ in-memory cooldown quên mật khẩu: email -> timestamp
_reset_cooldowns: dict[str, float] = {}
RESET_COOLDOWN_SECONDS = 60.0


def clear_auth_security_state() -> None:
    """Dọn dẹp bộ nhớ rate limit, cooldown và token revoked (dùng trong test)."""
    _failed_login_attempts.clear()
    _reset_cooldowns.clear()
    clear_revoked_tokens()


def login(db: Session, *, email: str, password: str) -> TokenPair:
    """Đăng nhập bằng email và mật khẩu (kèm bảo vệ Timing Attack & Brute-Force)."""
    normalized_email = email.strip().lower()
    now = time.monotonic()
    attempts = [
        t for t in _failed_login_attempts.get(normalized_email, [])
        if now - t < LOGIN_LOCKOUT_SECONDS
    ]
    _failed_login_attempts[normalized_email] = attempts
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise AppException(
            "Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau 1 phút.",
            code="TOO_MANY_ATTEMPTS",
            status_code=429,
        )

    user = db.scalars(
        select(User).where(func.lower(User.email) == normalized_email)
    ).first()

    if user is not None and user.status == UserStatus.PENDING_ACTIVATION and user.password_hash is None:
        raise ForbiddenError("Tài khoản chưa được kích hoạt", code="ACCOUNT_NOT_ACTIVE")

    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        _failed_login_attempts.setdefault(normalized_email, []).append(time.monotonic())
        raise UnauthorizedError("Email hoặc mật khẩu không đúng", code="INVALID_CREDENTIALS")

    if not verify_password(password, user.password_hash):
        _failed_login_attempts.setdefault(normalized_email, []).append(time.monotonic())
        raise UnauthorizedError("Email hoặc mật khẩu không đúng", code="INVALID_CREDENTIALS")

    # Mật khẩu chính xác -> xóa lịch sử thất bại
    _failed_login_attempts.pop(normalized_email, None)

    if user.status == UserStatus.LOCKED:
        raise ForbiddenError(
            user.locked_reason or "Tài khoản đã bị khóa",
            code="ACCOUNT_LOCKED",
        )
    if user.status == UserStatus.PENDING_ACTIVATION:
        raise ForbiddenError("Tài khoản chưa được kích hoạt", code="ACCOUNT_NOT_ACTIVE")
    if user.status == UserStatus.PENDING_APPROVAL:
        raise ForbiddenError(
            "Tài khoản đang chờ nhà trường phê duyệt",
            code="ACCOUNT_PENDING_APPROVAL",
        )
    if user.status != UserStatus.ACTIVE:
        raise ForbiddenError("Tài khoản chưa hoạt động", code="ACCOUNT_NOT_ACTIVE")

    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)

    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


def refresh_tokens(db: Session, refresh_token: str) -> TokenPair:
    """Đổi refresh token lấy cặp token mới (Refresh Token Rotation)."""
    payload = decode_token(refresh_token, expected_type="refresh")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Tài khoản không tồn tại")

    if user.status == UserStatus.LOCKED:
        raise ForbiddenError("Tài khoản đã bị khóa", code="ACCOUNT_LOCKED")
    if user.status != UserStatus.ACTIVE:
        raise ForbiddenError("Tài khoản chưa hoạt động", code="ACCOUNT_NOT_ACTIVE")

    # Xoay vòng Refresh Token: thu hồi token hiện tại
    revoke_token(refresh_token)

    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


def logout(access_token: str, refresh_token: Optional[str] = None) -> None:
    """Đăng xuất: thu hồi access_token và refresh_token (nếu có)."""
    revoke_token(access_token)
    if refresh_token:
        revoke_token(refresh_token)


def get_me(db: Session, user: User) -> User:
    """Lấy thông tin tài khoản hiện tại kèm hồ sơ liên kết theo role."""
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.student),
            selectinload(User.company),
            selectinload(User.admin),
        )
    )
    full_user = db.scalars(stmt).first()
    return full_user or user


def change_password(db: Session, user: User, data: ChangePasswordRequest) -> None:
    """Đổi mật khẩu cho user đang đăng nhập."""
    if not verify_password(data.old_password, user.password_hash):
        raise BadRequestError("Mật khẩu cũ không chính xác")

    if data.old_password == data.new_password:
        raise BadRequestError("Mật khẩu mới phải khác mật khẩu hiện tại")

    user.password_hash = hash_password(data.new_password)
    db.commit()


def create_activation_token(db: Session, user_id: int, *, commit: bool = True) -> str:
    """Sinh token ngẫu nhiên và lưu bản băm SHA-256 vào password_reset_tokens. Trả về token thô."""
    raw_token, token_hash = generate_reset_token()
    prt = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(prt)
    if commit:
        db.commit()
    else:
        db.flush()
    return raw_token


def request_password_reset(
    db: Session, background_tasks: BackgroundTasks, email: str
) -> Optional[str]:
    """Yêu cầu đặt lại mật khẩu. Gửi email nền nếu user hợp lệ (kèm cooldown chống spam)."""
    normalized_email = email.strip().lower()
    now = time.monotonic()
    last_time = _reset_cooldowns.get(normalized_email)
    if last_time is not None and now - last_time < RESET_COOLDOWN_SECONDS:
        return None

    user = db.scalars(
        select(User).where(func.lower(User.email) == normalized_email)
    ).first()

    # Chống dò quét tài khoản: không tìm thấy, bị khóa hoặc chưa kích hoạt thì không phát sinh reset
    if user is None or user.status in (UserStatus.LOCKED, UserStatus.PENDING_ACTIVATION):
        return None

    _reset_cooldowns[normalized_email] = time.monotonic()

    raw_token = create_activation_token(db, user.id, commit=True)
    subject, body_html = email_service.render_email_template(
        "PASSWORD_RESET",
        {
            "reset_token": raw_token,
            "email": user.email,
            "expires_minutes": settings.RESET_TOKEN_EXPIRE_MINUTES,
        },
    )
    email_service.queue_email(
        db,
        background_tasks,
        to_email=user.email,
        subject=subject,
        body_html=body_html,
        type="PASSWORD_RESET",
        user_id=user.id,
    )
    return raw_token


def reset_password(db: Session, data: ResetPasswordRequest) -> None:
    """Đặt lại mật khẩu mới bằng token."""
    token_hash = hash_token(data.token)
    prt = db.scalars(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).first()

    if prt is None:
        raise BadRequestError("Token đặt lại mật khẩu không hợp lệ", code="TOKEN_INVALID")
    if prt.used_at is not None:
        raise BadRequestError("Token đặt lại mật khẩu đã được sử dụng", code="TOKEN_USED")
    if prt.expires_at < utcnow():
        raise BadRequestError("Token đặt lại mật khẩu đã hết hạn", code="TOKEN_EXPIRED")

    user = db.get(User, prt.user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    if user.status == UserStatus.LOCKED:
        raise ForbiddenError("Tài khoản đã bị khóa", code="ACCOUNT_LOCKED")
    if user.status == UserStatus.PENDING_ACTIVATION:
        raise BadRequestError(
            "Tài khoản chưa được kích hoạt. Vui lòng sử dụng chức năng kích hoạt tài khoản.",
            code="ACCOUNT_NOT_ACTIVE",
        )

    now = utcnow()
    user.password_hash = hash_password(data.new_password)
    # Vô hiệu hóa toàn bộ token còn hiệu lực của user này
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .where(PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    db.commit()


def activate_student_account(db: Session, data: ActivateAccountRequest) -> None:
    """Kích hoạt tài khoản sinh viên do trường import."""
    token_hash = hash_token(data.token)
    prt = db.scalars(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).first()

    if prt is None:
        raise BadRequestError("Token kích hoạt không hợp lệ", code="TOKEN_INVALID")
    if prt.used_at is not None:
        raise BadRequestError("Token kích hoạt đã được sử dụng", code="TOKEN_USED")
    if prt.expires_at < utcnow():
        raise BadRequestError("Token kích hoạt đã hết hạn", code="TOKEN_EXPIRED")

    user = db.get(User, prt.user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    if user.role != UserRole.STUDENT:
        raise ForbiddenError("Chỉ tài khoản sinh viên mới sử dụng chức năng kích hoạt này")
    if user.status == UserStatus.LOCKED:
        raise ForbiddenError("Tài khoản đã bị khóa", code="ACCOUNT_LOCKED")
    if user.status == UserStatus.ACTIVE:
        raise ConflictError("Tài khoản đã được kích hoạt trước đó")
    if user.status != UserStatus.PENDING_ACTIVATION:
        raise BadRequestError("Tài khoản không ở trạng thái chờ kích hoạt")

    now = utcnow()
    user.password_hash = hash_password(data.new_password)
    user.status = UserStatus.ACTIVE
    # Vô hiệu hóa toàn bộ token còn hiệu lực của user này
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .where(PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    db.commit()


def register_company(db: Session, data: RegisterCompanyRequest) -> dict:
    """Đăng ký doanh nghiệp mới (chờ nhà trường phê duyệt)."""
    normalized_email = data.email.strip().lower()
    existing_user = db.scalars(
        select(User).where(func.lower(User.email) == normalized_email)
    ).first()
    if existing_user is not None:
        raise ConflictError("Email đã được sử dụng")

    tax_code = data.tax_code.strip()
    existing_company = db.scalars(
        select(Company).where(Company.tax_code == tax_code)
    ).first()
    if existing_company is not None:
        raise ConflictError("Mã số thuế đã được đăng ký")

    if data.industry_id is not None:
        industry = db.get(Industry, data.industry_id)
        if industry is None or not industry.is_active:
            raise NotFoundError("Không tìm thấy lĩnh vực hoạt động")

    user = User(
        email=normalized_email,
        password_hash=hash_password(data.password),
        role=UserRole.COMPANY,
        status=UserStatus.PENDING_APPROVAL,
    )
    db.add(user)
    db.flush()

    company = Company(
        user_id=user.id,
        name=data.company_name.strip(),
        tax_code=tax_code,
        industry_id=data.industry_id,
        address=data.address.strip() if data.address else None,
        website=data.website.strip() if data.website else None,
        contact_name=data.contact_name.strip() if data.contact_name else None,
        contact_phone=data.contact_phone.strip() if data.contact_phone else None,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    return {
        "user_id": user.id,
        "company_id": company.id,
        "email": user.email,
        "company_name": company.name,
        "tax_code": company.tax_code,
        "status": user.status,
        "verification_status": company.verification_status,
        "message": "Đăng ký tài khoản doanh nghiệp thành công. Vui lòng chờ nhà trường phê duyệt.",
    }
