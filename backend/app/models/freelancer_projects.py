"""Freelancer projects tables. Rules crossing rows belong in transactional services."""
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
from app.models.freelancer_base import UTCDateTime, state_type


class FreelanceProject(Base):
    __tablename__ = "freelance_projects"

    id: Mapped[int] = pk()
    client_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ID, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    budget_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False)
    recruitment_status: Mapped[fe.RecruitmentStatus] = mapped_column(state_type(fe.RecruitmentStatus, "freelance_projects_recruitment_status"), nullable=False, default='NOT_OPEN', server_default='NOT_OPEN')
    recruitment_closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    deadline: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    deliverables_description: Mapped[str] = mapped_column(Text, nullable=False)
    funding_policy: Mapped[fe.FundingPolicy] = mapped_column(state_type(fe.FundingPolicy, "freelance_projects_funding_policy"), nullable=False)
    status: Mapped[fe.ProjectStatus] = mapped_column(state_type(fe.ProjectStatus, "freelance_projects_status"), nullable=False, default='DRAFT', server_default='DRAFT')
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('budget_amount > 0', name='budget_amount_amount'),
        CheckConstraint('max_students > 0', name='max_students_nonnegative'),
        Index('ix_freelance_projects_client_user_id_status', 'client_user_id', 'status'),
        Index('ix_freelance_projects_company_id_status', 'company_id', 'status'),
        Index('ix_freelance_projects_status_recruitment_status_created_at', 'status', 'recruitment_status', 'created_at'),
        Index('ix_freelance_projects_client_user_id', 'client_user_id'),
        Index('ix_freelance_projects_company_id', 'company_id'),
        Index('ix_freelance_projects_reviewed_by', 'reviewed_by'),
    )


class ProjectMilestoneProposal(Base):
    __tablename__ = "project_milestone_proposals"

    id: Mapped[int] = pk()
    project_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_projects.id", ondelete="RESTRICT"), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('sequence_no > 0', name='sequence_no_nonnegative'),
        CheckConstraint('amount > 0', name='amount_amount'),
        UniqueConstraint('project_id', 'sequence_no', name='uq_project_milestone_proposals_project_id_sequence_no'),
    )


class FreelanceProjectSkill(Base):
    __tablename__ = "freelance_project_skills"

    project_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_projects.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    skill_id: Mapped[int] = mapped_column(ID, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    __table_args__ = (
        Index('ix_freelance_project_skills_project_id', 'project_id'),
        Index('ix_freelance_project_skills_skill_id', 'skill_id'),
    )


class FreelanceProjectReview(Base):
    __tablename__ = "freelance_project_reviews"

    id: Mapped[int] = pk()
    project_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_projects.id", ondelete="RESTRICT"), nullable=False)
    reviewed_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    decision: Mapped[fe.ProjectReviewDecision] = mapped_column(state_type(fe.ProjectReviewDecision, "freelance_project_reviews_decision"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    project_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_freelance_project_reviews_project_id_created_at', 'project_id', 'created_at'),
        Index('ix_freelance_project_reviews_project_id', 'project_id'),
        Index('ix_freelance_project_reviews_reviewed_by', 'reviewed_by'),
    )


class FreelanceApplication(Base):
    __tablename__ = "freelance_applications"

    id: Mapped[int] = pk()
    project_id: Mapped[int] = mapped_column(ID, ForeignKey("freelance_projects.id", ondelete="RESTRICT"), nullable=False)
    student_id: Mapped[int] = mapped_column(ID, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False)
    proposal: Mapped[str] = mapped_column(Text, nullable=False)
    quoted_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    estimated_days: Mapped[int] = mapped_column(Integer, nullable=False)
    cv_id: Mapped[int | None] = mapped_column(ID, ForeignKey("cvs.id", ondelete="RESTRICT"), nullable=True)
    cv_snapshot_file_id: Mapped[int | None] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=True)
    status: Mapped[fe.FreelanceApplicationStatus] = mapped_column(state_type(fe.FreelanceApplicationStatus, "freelance_applications_status"), nullable=False, default='SUBMITTED', server_default='SUBMITTED')
    selected_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('quoted_amount > 0', name='quoted_amount_amount'),
        CheckConstraint('estimated_days > 0', name='estimated_days_nonnegative'),
        UniqueConstraint('project_id', 'student_id', name='uq_freelance_applications_project_id_student_id'),
        Index('ix_freelance_applications_student_id_status_created_at', 'student_id', 'status', 'created_at'),
        Index('ix_freelance_applications_project_id_status', 'project_id', 'status'),
        Index('ix_freelance_applications_student_id', 'student_id'),
        Index('ix_freelance_applications_cv_id', 'cv_id'),
        Index('ix_freelance_applications_cv_snapshot_file_id', 'cv_snapshot_file_id'),
    )
