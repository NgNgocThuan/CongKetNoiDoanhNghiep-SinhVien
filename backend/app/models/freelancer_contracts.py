"""Freelancer contracts tables. Rules crossing rows belong in transactional services."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core import freelancer_enums as fe
from app.models.base import ID, Base, USmallInt, pk
from app.models.freelancer_base import UTCDateTime, binary_string, state_type


class FreelanceContract(Base):
    __tablename__ = "freelance_contracts"

    id: Mapped[int] = pk()
    project_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_projects.id", ondelete="RESTRICT"), nullable=False)
    application_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_applications.id", ondelete="RESTRICT"), nullable=False, unique=True)
    client_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ID, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True)
    freelancer_student_id: Mapped[int] = mapped_column(ID, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[fe.ContractStatus] = mapped_column(state_type(fe.ContractStatus, "freelance_contracts_status"), nullable=False, default='DRAFT', server_default='DRAFT')
    effective_version_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('project_id', 'freelancer_student_id', name='uq_freelance_contracts_project_id_freelancer_student_id'),
        UniqueConstraint('project_id', 'id', name='uq_freelance_contracts_project_id_id'),
        Index('ix_freelance_contracts_client_user_id_status', 'client_user_id', 'status'),
        Index('ix_freelance_contracts_freelancer_student_id_status', 'freelancer_student_id', 'status'),
        Index('ix_freelance_contracts_project_id_status', 'project_id', 'status'),
        ForeignKeyConstraint(['id', 'effective_version_id'], ['contract_versions.contract_id', 'contract_versions.id'], name='fk_fc_effective_version', ondelete="RESTRICT", use_alter=True),
        Index('ix_freelance_contracts_application_id', 'application_id'),
        Index('ix_freelance_contracts_client_user_id', 'client_user_id'),
        Index('ix_freelance_contracts_company_id', 'company_id'),
        Index('ix_freelance_contracts_freelancer_student_id', 'freelancer_student_id'),
    )


class ProjectContractBudget(Base):
    __tablename__ = "project_contract_budgets"

    id: Mapped[int] = pk()
    project_id: Mapped[int] = mapped_column(ID, nullable=False)
    contract_id: Mapped[int] = mapped_column(ID, nullable=False)
    allocated_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[fe.ContractBudgetStatus] = mapped_column(state_type(fe.ContractBudgetStatus, "project_contract_budgets_status"), nullable=False, default='RESERVED', server_default='RESERVED')
    committed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('allocated_amount > 0', name='allocated_amount_amount'),
        UniqueConstraint('contract_id', name='uq_project_contract_budgets_contract_id'),
        ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name='fk_pcb_project', ondelete="RESTRICT", use_alter=False),
        ForeignKeyConstraint(['project_id', 'contract_id'], ['freelance_contracts.project_id', 'freelance_contracts.id'], name='fk_pcb_contract', ondelete="RESTRICT", use_alter=False),
        Index('ix_project_contract_budgets_project_id_status', 'project_id', 'status'),
    )


class ContractVersion(Base):
    __tablename__ = "contract_versions"

    id: Mapped[int] = pk()
    contract_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_contracts.id", ondelete="RESTRICT"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[fe.ContractVersionStatus] = mapped_column(state_type(fe.ContractVersionStatus, "contract_versions_status"), nullable=False, default='DRAFT', server_default='DRAFT')
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fee_rate_bp: Mapped[int] = mapped_column(USmallInt, nullable=False)
    review_period_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    max_revision_count: Mapped[int] = mapped_column(Integer, nullable=False)
    grace_period_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    funding_policy: Mapped[fe.FundingPolicy] = mapped_column(state_type(fe.FundingPolicy, "contract_versions_funding_policy"), nullable=False)
    terms_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(binary_string(64), nullable=True)
    offered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    acceptance_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    client_accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    freelancer_accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    effective_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    response_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('version_no > 0', name='version_no_nonnegative'),
        CheckConstraint('total_amount > 0', name='total_amount_amount'),
        CheckConstraint('fee_rate_bp >= 0', name='fee_rate_bp_nonnegative'),
        CheckConstraint('fee_rate_bp <= 10000', name='fee_rate_bp_range'),
        CheckConstraint('review_period_seconds > 0', name='review_period_seconds_nonnegative'),
        CheckConstraint('max_revision_count >= 0', name='max_revision_count_nonnegative'),
        CheckConstraint('grace_period_seconds >= 0', name='grace_period_seconds_nonnegative'),
        UniqueConstraint('contract_id', 'version_no', name='uq_contract_versions_contract_id_version_no'),
        UniqueConstraint('contract_id', 'id', name='uq_contract_versions_contract_id_id'),
        CheckConstraint('fee_rate_bp < 10000', name='fee_below_gross'),
        Index('ix_contract_versions_created_by', 'created_by'),
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = pk()
    contract_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_contracts.id", ondelete="RESTRICT"), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_terms_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    status: Mapped[fe.MilestoneStatus] = mapped_column(state_type(fe.MilestoneStatus, "milestones_status"), nullable=False, default='NOT_FUNDED', server_default='NOT_FUNDED')
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    review_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    acceptance_source: Mapped[fe.AcceptanceSource | None] = mapped_column(state_type(fe.AcceptanceSource, "milestones_acceptance_source"), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('sequence_no > 0', name='sequence_no_nonnegative'),
        CheckConstraint('revision_count >= 0', name='revision_count_nonnegative'),
        UniqueConstraint('contract_id', 'sequence_no', name='uq_milestones_contract_id_sequence_no'),
        UniqueConstraint('contract_id', 'id', name='uq_milestones_contract_id_id'),
        Index('ix_milestones_status_review_deadline', 'status', 'review_deadline'),
        ForeignKeyConstraint(['id', 'effective_terms_id'], ['contract_milestone_terms.milestone_id', 'contract_milestone_terms.id'], name='fk_ms_effective_terms', ondelete="RESTRICT", use_alter=True),
    )


class ContractMilestoneTerm(Base):
    __tablename__ = "contract_milestone_terms"

    id: Mapped[int] = pk()
    contract_id: Mapped[int] = mapped_column(ID, nullable=False)
    contract_version_id: Mapped[int] = mapped_column(ID, nullable=False)
    milestone_id: Mapped[int] = mapped_column(ID, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_amount'),
        UniqueConstraint('contract_version_id', 'milestone_id', name='uq_contract_milestone_terms_contract_version_id_milestone_id'),
        UniqueConstraint('milestone_id', 'id', name='uq_contract_milestone_terms_milestone_id_id'),
        ForeignKeyConstraint(['contract_id', 'contract_version_id'], ['contract_versions.contract_id', 'contract_versions.id'], name='fk_cmt_version', ondelete="RESTRICT", use_alter=False),
        ForeignKeyConstraint(['contract_id', 'milestone_id'], ['milestones.contract_id', 'milestones.id'], name='fk_cmt_milestone', ondelete="RESTRICT", use_alter=False),
    )


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False)
    submission_no: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('submission_no > 0', name='submission_no_nonnegative'),
        UniqueConstraint('milestone_id', 'submission_no', name='uq_deliverables_milestone_id_submission_no'),
        UniqueConstraint('milestone_id', 'id', name='uq_deliverables_milestone_id_id'),
        Index('ix_deliverables_submitted_by', 'submitted_by'),
    )


class DeliverableFile(Base):
    __tablename__ = "deliverable_files"

    deliverable_id: Mapped[int] = mapped_column(ID, ForeignKey("deliverables.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    file_id: Mapped[int] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_deliverable_files_deliverable_id', 'deliverable_id'),
        Index('ix_deliverable_files_file_id', 'file_id'),
    )


class MilestoneReview(Base):
    __tablename__ = "milestone_reviews"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, nullable=False)
    deliverable_id: Mapped[int] = mapped_column(ID, nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    action: Mapped[fe.MilestoneReviewAction] = mapped_column(state_type(fe.MilestoneReviewAction, "milestone_reviews_action"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(['milestone_id', 'deliverable_id'], ['deliverables.milestone_id', 'deliverables.id'], name='fk_mr_deliverable', ondelete="RESTRICT", use_alter=False),
        Index('ix_milestone_reviews_milestone_id_created_at', 'milestone_id', 'created_at'),
        Index('ix_milestone_reviews_reviewed_by', 'reviewed_by'),
    )


class FreelanceReview(Base):
    __tablename__ = "freelance_reviews"

    id: Mapped[int] = pk()
    contract_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_contracts.id", ondelete="RESTRICT"), nullable=False)
    reviewer_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reviewee_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[fe.ReviewVisibility] = mapped_column(state_type(fe.ReviewVisibility, "freelance_reviews_visibility"), nullable=False, default='VISIBLE', server_default='VISIBLE')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('rating > 0', name='rating_nonnegative'),
        UniqueConstraint('contract_id', 'reviewer_user_id', name='uq_freelance_reviews_contract_id_reviewer_user_id'),
        CheckConstraint('rating <= 5', name='rating_range'),
        CheckConstraint('reviewer_user_id <> reviewee_user_id', name='distinct_reviewers'),
        Index('ix_freelance_reviews_reviewer_user_id', 'reviewer_user_id'),
        Index('ix_freelance_reviews_reviewee_user_id', 'reviewee_user_id'),
    )
