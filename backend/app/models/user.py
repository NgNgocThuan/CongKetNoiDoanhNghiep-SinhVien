"""Tài khoản đăng nhập và token đặt lại mật khẩu."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CHAR, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserRole, UserStatus
from app.models.base import Base, CreatedAtMixin, TimestampMixin, db_enum, fk, pk

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.school import Admin
    from app.models.student import Student


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))  # NULL khi chưa kích hoạt
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        db_enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING_ACTIVATION,
        server_default=UserStatus.PENDING_ACTIVATION.value,
    )
    locked_reason: Mapped[Optional[str]] = mapped_column(String(500))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Mỗi user thuộc đúng một loại hồ sơ, tùy role
    student: Mapped[Optional["Student"]] = relationship(back_populates="user", uselist=False)
    company: Mapped[Optional["Company"]] = relationship(
        back_populates="user", uselist=False, foreign_keys="Company.user_id"
    )
    admin: Mapped[Optional["Admin"]] = relationship(back_populates="user", uselist=False)

    __table_args__ = (Index("idx_users_role_status", "role", "status"),)


class PasswordResetToken(CreatedAtMixin, Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (Index("idx_prt_user", "user_id"),)
