"""Runtime policy, OTP abuse counters and mutual dispute withdrawal records."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ID, Base, pk
from app.models.freelancer_base import UTCDateTime, binary_string


class FreelancerPolicy(Base):
    __tablename__ = "freelancer_policies"
    id: Mapped[int] = pk()
    policy_key: Mapped[str] = mapped_column(binary_string(50), unique=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    values_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_by: Mapped[int | None] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, server_default=func.now()
    )
    __table_args__ = (CheckConstraint("revision > 0", name="revision_positive"),)


class OtpRateBucket(Base):
    __tablename__ = "otp_rate_buckets"
    id: Mapped[int] = pk()
    scope_hash: Mapped[str] = mapped_column(binary_string(64), unique=True, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    __table_args__ = (CheckConstraint("count >= 0", name="count_nonnegative"),)


class DisputeWithdrawal(Base):
    __tablename__ = "dispute_withdrawals"
    id: Mapped[int] = pk()
    dispute_id: Mapped[int] = mapped_column(
        ID, ForeignKey("disputes.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    requested_by: Mapped[int] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    terms_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    confirmed_by: Mapped[int | None] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    __table_args__ = (
        CheckConstraint(
            "confirmed_by IS NULL OR confirmed_by <> requested_by", name="distinct_confirmers"
        ),
    )


class ProjectExpansion(Base):
    __tablename__ = "project_expansions"
    id: Mapped[int] = pk()
    project_id: Mapped[int] = mapped_column(
        ID, ForeignKey("freelance_projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    requested_by: Mapped[int] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    request_key: Mapped[str] = mapped_column(binary_string(128), nullable=False)
    budget_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    review_reason: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint(
            "project_id", "request_key", name="uq_project_expansions_project_id_request_key"
        ),
        CheckConstraint("budget_amount > 0 AND max_students > 0", name="positive_ceilings"),
        CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name="status_values"),
    )
