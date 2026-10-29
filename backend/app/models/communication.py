"""Thông báo trong ứng dụng, nhật ký email, báo cáo vi phạm."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import EmailStatus, ReportStatus, ReportTargetType
from app.models.base import ID, Base, CreatedAtMixin, UTinyInt, db_enum, fk, pk


class Notification(CreatedAtMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # APPLICATION_STATUS, JOB_APPROVED...
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    ref_type: Mapped[Optional[str]] = mapped_column(String(30))
    ref_id: Mapped[Optional[int]] = mapped_column(ID)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())

    __table_args__ = (Index("idx_notifications_user", "user_id", "is_read", "created_at"),)


class EmailLog(CreatedAtMixin, Base):
    __tablename__ = "email_logs"

    id: Mapped[int] = pk()
    user_id: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # APPLY_SUCCESS, STATUS_CHANGED...
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[EmailStatus] = mapped_column(
        db_enum(EmailStatus), nullable=False, default=EmailStatus.PENDING, server_default=EmailStatus.PENDING.value
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    retry_count: Mapped[int] = mapped_column(UTinyInt, nullable=False, default=0, server_default="0")
    ref_type: Mapped[Optional[str]] = mapped_column(String(30))
    ref_id: Mapped[Optional[int]] = mapped_column(ID)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("idx_email_logs_status", "status", "created_at"),
        Index("idx_email_logs_ref", "ref_type", "ref_id"),
        Index("idx_email_logs_user", "user_id"),
    )


class Report(CreatedAtMixin, Base):
    """Báo cáo vi phạm về tin tuyển dụng / doanh nghiệp / sinh viên."""

    __tablename__ = "reports"

    id: Mapped[int] = pk()
    reporter_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    target_type: Mapped[ReportTargetType] = mapped_column(db_enum(ReportTargetType), nullable=False)
    target_id: Mapped[int] = mapped_column(ID, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        db_enum(ReportStatus), nullable=False, default=ReportStatus.PENDING, server_default=ReportStatus.PENDING.value
    )
    handled_by: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_note: Mapped[Optional[str]] = mapped_column(String(500))

    __table_args__ = (
        Index("idx_reports_target", "target_type", "target_id"),
        Index("idx_reports_status", "status", "created_at"),
    )
