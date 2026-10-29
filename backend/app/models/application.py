"""Lời mời ứng tuyển, đơn ứng tuyển, lịch sử trạng thái.

Không có bảng lịch phỏng vấn: khi đơn chuyển sang INTERVIEW, doanh nghiệp tự gửi email lịch cho sinh viên
(nội dung có thể gửi qua email_service và lưu ở application_status_logs.note).
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApplicationStatus, InvitationStatus
from app.models.base import Base, CreatedAtMixin, db_enum, fk, pk

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.student import CV, Student


class Invitation(CreatedAtMixin, Base):
    """Doanh nghiệp mời sinh viên ứng tuyển (từ gợi ý ứng viên AI)."""

    __tablename__ = "invitations"

    id: Mapped[int] = pk()
    company_id: Mapped[int] = fk("companies.id", ondelete="CASCADE")
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    job_id: Mapped[int] = fk("jobs.id", ondelete="CASCADE")
    message: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[InvitationStatus] = mapped_column(
        db_enum(InvitationStatus),
        nullable=False,
        default=InvitationStatus.PENDING,
        server_default=InvitationStatus.PENDING.value,
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        UniqueConstraint("job_id", "student_id", name="uq_invitations_job_student"),
        Index("idx_invitations_student", "student_id", "status"),
        Index("idx_invitations_company", "company_id"),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    job_id: Mapped[int] = fk("jobs.id", ondelete="CASCADE")
    cv_id: Mapped[int] = fk("cvs.id")
    cv_snapshot_url: Mapped[Optional[str]] = mapped_column(String(500))  # bản CV tại thời điểm nộp
    cover_letter: Mapped[Optional[str]] = mapped_column(Text)
    invitation_id: Mapped[Optional[int]] = fk("invitations.id", ondelete="SET NULL", nullable=True)
    current_status: Mapped[ApplicationStatus] = mapped_column(
        db_enum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.APPLIED,
        server_default=ApplicationStatus.APPLIED.value,
    )
    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="applications")
    job: Mapped["Job"] = relationship(back_populates="applications")
    cv: Mapped["CV"] = relationship()
    status_logs: Mapped[list["ApplicationStatusLog"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationStatusLog.changed_at"
    )

    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_applications_student_job"),
        Index("idx_applications_job_status", "job_id", "current_status"),
        Index("idx_applications_cv", "cv_id"),
    )


class ApplicationStatusLog(Base):
    __tablename__ = "application_status_logs"

    id: Mapped[int] = pk()
    application_id: Mapped[int] = fk("applications.id", ondelete="CASCADE")
    old_status: Mapped[Optional[str]] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500))
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="status_logs")

    __table_args__ = (Index("idx_asl_application", "application_id", "changed_at"),)
