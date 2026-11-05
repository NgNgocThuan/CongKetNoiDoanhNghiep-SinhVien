"""FastAPI router for mutual contract reviews."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, status

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole
from app.core.freelancer_enums import ActorType
from app.dependencies import CurrentUser, DbSession
from app.models.freelancer_contracts import FreelanceReview
from app.schemas.freelance_reviews import (
    FreelanceReviewCreate,
    FreelanceReviewRead,
)
from app.services.freelance_review_service import FreelanceReviewService

router = APIRouter(tags=["Freelance Reviews"])
service = FreelanceReviewService()


def _build_context(user: CurrentUser, request_id: str | None, idempotency_key: str | None) -> CommandContext:
    return CommandContext(
        actor_user_id=user.id,
        actor_type=ActorType.USER,
        request_id=request_id or str(uuid.uuid4()),
        idempotency_key=idempotency_key,
        now_utc=datetime.now(timezone.utc),
    )


def _format_review(review: FreelanceReview) -> FreelanceReviewRead:
    return FreelanceReviewRead(
        id=review.id,
        contract_id=review.contract_id,
        reviewer_user_id=review.reviewer_user_id,
        reviewee_user_id=review.reviewee_user_id,
        rating=review.rating,
        comment=review.comment,
        visibility=review.visibility,
        created_at=review.created_at,
    )


@router.get("/freelance-contracts/{contract_id}/reviews", response_model=list[FreelanceReviewRead])
def list_contract_reviews(
    contract_id: int,
    db: DbSession,
    user: CurrentUser,
):
    reviews = service.get_contract_reviews(
        db,
        contract_id=contract_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return [
        FreelanceReviewRead(
            id=r.id,
            contract_id=r.contract_id,
            reviewer_user_id=r.reviewer_user_id,
            reviewee_user_id=r.reviewee_user_id,
            rating=r.rating,
            comment=r.comment,
            visibility=r.visibility,
            created_at=r.created_at,
        )
        for r in reviews
    ]


@router.post("/freelance-contracts/{contract_id}/reviews", response_model=FreelanceReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(
    contract_id: int,
    payload: FreelanceReviewCreate,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    review = service.create_review(
        db,
        ctx=ctx,
        contract_id=contract_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    return FreelanceReviewRead(
        id=review.id,
        contract_id=review.contract_id,
        reviewer_user_id=review.reviewer_user_id,
        reviewee_user_id=review.reviewee_user_id,
        rating=review.rating,
        comment=review.comment,
        visibility=review.visibility,
        created_at=review.created_at,
    )
