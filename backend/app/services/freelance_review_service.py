"""Freelance review service: Mutual 2-way post-terminal evaluations (Ticket C6)."""
from sqlalchemy.orm import Session

from app.contracts.freelancer.types import CommandContext
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableError,
)
from app.core.freelancer_enums import (
    ContractStatus,
    MilestoneStatus,
    ReviewVisibility,
)
from app.models import FreelanceProject, Student
from app.models.freelancer_contracts import (
    FreelanceContract,
    FreelanceReview,
    Milestone,
)
from app.models.freelancer_operations import AuditLog
from app.services.freelancer_commands import run_command


def _for_update(query, db: Session):
    bind = db.get_bind()
    if bind is not None and bind.dialect.name != "sqlite":
        return query.with_for_update()
    return query


class FreelanceReviewService:
    """Manages two-way contract reviews after terminal settlement."""

    def create_review_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
        rating: int,
        comment: str | None = None,
    ) -> FreelanceReview:
        """Create a review for a terminal contract that had paid out work."""
        contract_raw = db.get(FreelanceContract, contract_id)
        if not contract_raw:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # Global lock ordering: project -> contract
        _for_update(db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db).first()
        contract = _for_update(db.query(FreelanceContract).filter_by(id=contract_raw.id), db).first()

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # Rating range validation
        if not (1 <= rating <= 5):
            raise UnprocessableError("Rating must be between 1 and 5", code="VALIDATION_ERROR")

        # Determine reviewee
        if ctx.actor_user_id == contract.client_user_id:
            reviewee_user_id = student.user_id
        else:
            reviewee_user_id = contract.client_user_id

        # Contract terminal status check
        if contract.status not in (ContractStatus.COMPLETED, ContractStatus.TERMINATED):
            raise ConflictError("Contract must be completed or terminated before reviewing", code="INVALID_STATE_TRANSITION")

        # Spec 7.7 invariant: Paid work required
        has_paid_work = db.query(Milestone).filter(
            Milestone.contract_id == contract.id,
            Milestone.status.in_([MilestoneStatus.PAID_OUT, MilestoneStatus.PARTIALLY_RELEASED]),
        ).first() is not None

        if not has_paid_work:
            raise ConflictError(
                "Reviews are only allowed when at least one milestone has been paid out or partially released",
                code="INVALID_STATE_TRANSITION",
            )

        # Unique review per party
        existing = db.query(FreelanceReview).filter_by(
            contract_id=contract.id,
            reviewer_user_id=ctx.actor_user_id,
        ).first()
        if existing:
            raise ConflictError("You have already reviewed this contract", code="INVALID_STATE_TRANSITION")

        review = FreelanceReview(
            contract_id=contract.id,
            reviewer_user_id=ctx.actor_user_id,
            reviewee_user_id=reviewee_user_id,
            rating=rating,
            comment=comment.strip() if comment else None,
            visibility=ReviewVisibility.VISIBLE,
        )
        db.add(review)
        db.flush()

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_review.created",
                entity_type="freelance_reviews",
                entity_id=review.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return review

    def create_review(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
        rating: int,
        comment: str | None = None,
    ) -> FreelanceReview:
        return run_command(
            db,
            lambda: self.create_review_in_tx(
                db, ctx=ctx, contract_id=contract_id, rating=rating, comment=comment,
            ),
        )

    def get_contract_reviews(
        self,
        db: Session,
        *,
        contract_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> list[FreelanceReview]:
        """Fetch reviews for a contract ensuring zero-leak visibility rules."""
        contract = db.get(FreelanceContract, contract_id)
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if not is_admin:
            student = db.get(Student, contract.freelancer_student_id)
            if not student or actor_user_id not in (contract.client_user_id, student.user_id):
                raise NotFoundError("Contract not found", code="NOT_FOUND")

        query = db.query(FreelanceReview).filter_by(contract_id=contract_id)
        if not is_admin:
            query = query.filter_by(visibility=ReviewVisibility.VISIBLE)

        return query.order_by(FreelanceReview.created_at.asc()).all()
