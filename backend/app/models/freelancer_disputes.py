"""Freelancer disputes tables. Rules crossing rows belong in transactional services."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core import freelancer_enums as fe
from app.models.base import ID, Base, pk
from app.models.freelancer_base import UTCDateTime, binary_string, state_type


class CancellationAgreement(Base):
    __tablename__ = "cancellation_agreements"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False)
    requested_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    basis: Mapped[fe.CancellationBasis] = mapped_column(state_type(fe.CancellationBasis, "cancellation_agreements_basis"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    freelancer_gross: Mapped[int] = mapped_column(BigInteger, nullable=False)
    refund_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    terms_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    status: Mapped[fe.CancellationStatus] = mapped_column(state_type(fe.CancellationStatus, "cancellation_agreements_status"), nullable=False, default='PROPOSED', server_default='PROPOSED')
    client_accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    freelancer_accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    policy_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('freelancer_gross >= 0', name='freelancer_gross_amount'),
        CheckConstraint('refund_amount >= 0', name='refund_amount_amount'),
        Index('ix_cancellation_agreements_milestone_id_status', 'milestone_id', 'status'),
        Index('ix_cancellation_agreements_milestone_id', 'milestone_id'),
        Index('ix_cancellation_agreements_requested_by', 'requested_by'),
    )


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False)
    opened_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[fe.DisputeStatus] = mapped_column(state_type(fe.DisputeStatus, "disputes_status"), nullable=False, default='OPEN', server_default='OPEN')
    previous_milestone_status: Mapped[fe.MilestoneStatus] = mapped_column(state_type(fe.MilestoneStatus, "disputes_previous_milestone_status"), nullable=False)
    remaining_review_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_deadline: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    assigned_admin_id: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    withdrawal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('remaining_review_seconds >= 0', name='remaining_review_seconds_nonnegative'),
        Index('ix_disputes_status_evidence_deadline', 'status', 'evidence_deadline'),
        Index('ix_disputes_milestone_id_created_at', 'milestone_id', 'created_at'),
        Index('ix_disputes_milestone_id', 'milestone_id'),
        Index('ix_disputes_opened_by', 'opened_by'),
        Index('ix_disputes_assigned_admin_id', 'assigned_admin_id'),
    )


class ActiveMilestoneDispute(Base):
    __tablename__ = "active_milestone_disputes"

    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    dispute_id: Mapped[int] = mapped_column(ID, ForeignKey("disputes.id", ondelete="RESTRICT"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_active_milestone_disputes_milestone_id', 'milestone_id'),
        Index('ix_active_milestone_disputes_dispute_id', 'dispute_id'),
    )


class MilestoneHold(Base):
    __tablename__ = "milestone_holds"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False)
    reason_type: Mapped[fe.HoldReason] = mapped_column(state_type(fe.HoldReason, "milestone_holds_reason_type"), nullable=False)
    reason_key: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    dispute_id: Mapped[int | None] = mapped_column(ID, ForeignKey("disputes.id", ondelete="RESTRICT"), nullable=True)
    placed_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    placed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    released_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    release_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_milestone_holds_milestone_id_released_at', 'milestone_id', 'released_at'),
        Index('ix_milestone_holds_milestone_id', 'milestone_id'),
        Index('ix_milestone_holds_dispute_id', 'dispute_id'),
        Index('ix_milestone_holds_placed_by', 'placed_by'),
        Index('ix_milestone_holds_released_by', 'released_by'),
    )


class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"

    id: Mapped[int] = pk()
    dispute_id: Mapped[int] = mapped_column(ID, ForeignKey("disputes.id", ondelete="RESTRICT"), nullable=False)
    submitted_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    file_id: Mapped[int | None] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=True)
    deliverable_id: Mapped[int | None] = mapped_column(ID, ForeignKey("deliverables.id", ondelete="RESTRICT"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('file_id IS NOT NULL OR deliverable_id IS NOT NULL OR note IS NOT NULL', name='has_evidence'),
        Index('ix_dispute_evidence_dispute_id_created_at', 'dispute_id', 'created_at'),
        Index('ix_dispute_evidence_dispute_id', 'dispute_id'),
        Index('ix_dispute_evidence_submitted_by', 'submitted_by'),
        Index('ix_dispute_evidence_file_id', 'file_id'),
        Index('ix_dispute_evidence_deliverable_id', 'deliverable_id'),
    )


class DisputeDecision(Base):
    __tablename__ = "dispute_decisions"

    id: Mapped[int] = pk()
    dispute_id: Mapped[int] = mapped_column(ID, ForeignKey("disputes.id", ondelete="RESTRICT"), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[fe.DisputeOutcome] = mapped_column(state_type(fe.DisputeOutcome, "dispute_decisions_outcome"), nullable=False)
    freelancer_gross: Mapped[int] = mapped_column(BigInteger, nullable=False)
    refund_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[fe.DisputeDecisionStatus] = mapped_column(state_type(fe.DisputeDecisionStatus, "dispute_decisions_status"), nullable=False, default='PROPOSED', server_default='PROPOSED')
    requires_second_approval: Mapped[bool] = mapped_column(Boolean, nullable=False)
    approval_threshold_snapshot: Mapped[int] = mapped_column(BigInteger, nullable=False)
    proposed_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('revision_no > 0', name='revision_no_nonnegative'),
        CheckConstraint('freelancer_gross >= 0', name='freelancer_gross_amount'),
        CheckConstraint('refund_amount >= 0', name='refund_amount_amount'),
        CheckConstraint('approval_threshold_snapshot >= 0', name='approval_threshold_snapshot_amount'),
        UniqueConstraint('dispute_id', 'revision_no', name='uq_dispute_decisions_dispute_id_revision_no'),
        CheckConstraint('approved_by IS NULL OR approved_by <> proposed_by', name='distinct_approvers'),
        CheckConstraint("(outcome = 'PAYOUT' AND freelancer_gross > 0 AND refund_amount = 0) OR (outcome = 'REFUND' AND freelancer_gross = 0 AND refund_amount > 0) OR (outcome = 'SPLIT' AND freelancer_gross > 0 AND refund_amount > 0)", name='decision_amounts'),
        Index('ix_dispute_decisions_proposed_by', 'proposed_by'),
        Index('ix_dispute_decisions_approved_by', 'approved_by'),
    )
