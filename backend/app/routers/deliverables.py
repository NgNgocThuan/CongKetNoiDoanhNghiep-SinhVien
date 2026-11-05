"""FastAPI router for deliverables and submissions history."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, status

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole
from app.core.freelancer_enums import ActorType
from app.dependencies import CurrentUser, DbSession
from app.models.freelancer_contracts import (
    Deliverable,
    DeliverableFile,
    MilestoneReview,
)
from app.schemas.deliverables import (
    DeliverableCreate,
    DeliverableFileRead,
    DeliverableRead,
    MilestoneReviewRead,
)
from app.services.deliverable_service import DeliverableService

router = APIRouter(tags=["Freelance Deliverables"])
service = DeliverableService()


def _build_context(user: CurrentUser, request_id: str | None, idempotency_key: str | None) -> CommandContext:
    return CommandContext(
        actor_user_id=user.id,
        actor_type=ActorType.USER,
        request_id=request_id or str(uuid.uuid4()),
        idempotency_key=idempotency_key,
        now_utc=datetime.now(timezone.utc),
    )


def _format_deliverable(db: DbSession, deliverable: Deliverable) -> DeliverableRead:
    files = db.query(DeliverableFile).filter_by(deliverable_id=deliverable.id).all()
    files_read = [
        DeliverableFileRead(file_id=f.file_id, created_at=f.created_at)
        for f in files
    ]
    reviews = db.query(MilestoneReview).filter_by(deliverable_id=deliverable.id).all()
    reviews_read = [
        MilestoneReviewRead(
            id=r.id,
            milestone_id=r.milestone_id,
            deliverable_id=r.deliverable_id,
            reviewed_by=r.reviewed_by,
            action=r.action,
            reason=r.reason,
            reviewed_at=r.reviewed_at,
        )
        for r in reviews
    ]
    return DeliverableRead(
        id=deliverable.id,
        milestone_id=deliverable.milestone_id,
        submission_no=deliverable.submission_no,
        submitted_by=deliverable.submitted_by,
        note=deliverable.note,
        submitted_at=deliverable.submitted_at,
        files=files_read,
        reviews=reviews_read,
    )


@router.get("/milestones/{milestone_id}/deliverables", response_model=list[DeliverableRead])
def list_deliverables(
    milestone_id: int,
    db: DbSession,
    user: CurrentUser,
):
    deliverables = service.get_deliverables(
        db,
        milestone_id=milestone_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return [_format_deliverable(db, d) for d in deliverables]


@router.post("/milestones/{milestone_id}/deliverables", response_model=DeliverableRead, status_code=status.HTTP_201_CREATED)
def submit_deliverable(
    milestone_id: int,
    payload: DeliverableCreate,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    deliverable = service.submit_deliverable(
        db,
        ctx=ctx,
        milestone_id=milestone_id,
        file_ids=payload.file_ids,
        note=payload.note,
    )
    return _format_deliverable(db, deliverable)
