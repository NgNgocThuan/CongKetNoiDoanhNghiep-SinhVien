"""FastAPI router for freelance milestones and work lifecycle."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header

from app.contracts.freelancer.ports import FinancePort
from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole
from app.core.freelancer_enums import ActorType
from app.dependencies import CurrentUser, DbSession
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    Milestone,
)
from app.schemas.deliverables import MilestoneReviewRead
from app.schemas.freelance_contracts import ContractMilestoneTermRead
from app.schemas.milestones import (
    MilestoneAcceptRequest,
    MilestoneRead,
    MilestoneRevisionRequest,
)
from app.services.deliverable_service import (
    DeliverableService,
    accept_milestone_command,
)
from app.services.freelancer_finance import get_finance_port
from app.services.milestone_service import MilestoneService

router = APIRouter(tags=["Freelance Milestones"])
milestone_service = MilestoneService()
deliverable_service = DeliverableService()


def _build_context(
    user: CurrentUser, request_id: str | None, idempotency_key: str | None
) -> CommandContext:
    return CommandContext(
        actor_user_id=user.id,
        actor_type=ActorType.USER,
        request_id=request_id or str(uuid.uuid4()),
        idempotency_key=idempotency_key,
        now_utc=datetime.now(timezone.utc),
    )


def _format_milestone(
    db: DbSession, milestone: Milestone, *, settlement_id: int | None = None
) -> MilestoneRead:
    eff_term = None
    if milestone.effective_terms_id:
        t = db.get(ContractMilestoneTerm, milestone.effective_terms_id)
        if t:
            eff_term = ContractMilestoneTermRead(
                id=t.id,
                milestone_id=t.milestone_id,
                title=t.title,
                description=t.description,
                amount=t.amount,
                acceptance_criteria=t.acceptance_criteria,
                due_at=t.due_at,
                included=t.included,
            )

    return MilestoneRead(
        id=milestone.id,
        contract_id=milestone.contract_id,
        sequence_no=milestone.sequence_no,
        effective_terms_id=milestone.effective_terms_id,
        status=milestone.status,
        started_at=milestone.started_at,
        submitted_at=milestone.submitted_at,
        review_deadline=milestone.review_deadline,
        revision_count=milestone.revision_count,
        accepted_at=milestone.accepted_at,
        acceptance_source=milestone.acceptance_source,
        settled_at=milestone.settled_at,
        settlement_id=settlement_id,
        created_at=milestone.created_at,
        effective_terms=eff_term,
    )


@router.get("/freelance-contracts/{contract_id}/milestones", response_model=list[MilestoneRead])
def list_contract_milestones(
    contract_id: int,
    db: DbSession,
    user: CurrentUser,
):
    milestones = milestone_service.get_contract_milestones(
        db,
        contract_id=contract_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return [_format_milestone(db, m) for m in milestones]


@router.get("/milestones/{milestone_id}", response_model=MilestoneRead)
def get_milestone(
    milestone_id: int,
    db: DbSession,
    user: CurrentUser,
):
    milestone = milestone_service.get_milestone(
        db,
        milestone_id=milestone_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return _format_milestone(db, milestone)


@router.post("/milestones/{milestone_id}/start", response_model=MilestoneRead)
def start_milestone(
    milestone_id: int,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
    finance_port: FinancePort = Depends(get_finance_port),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    milestone = milestone_service.start_milestone(
        db,
        ctx=ctx,
        milestone_id=milestone_id,
        finance_port=finance_port,
    )
    return _format_milestone(db, milestone)


@router.post("/milestones/{milestone_id}/accept", response_model=MilestoneRead)
def accept_milestone_endpoint(
    milestone_id: int,
    payload: MilestoneAcceptRequest,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
    finance_port: FinancePort = Depends(get_finance_port),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    settlement_ref = accept_milestone_command(
        db,
        ctx=ctx,
        milestone_id=milestone_id,
        deliverable_id=payload.deliverable_id,
        finance_port=finance_port,
        automatic=False,
    )
    milestone = milestone_service.get_milestone(
        db,
        milestone_id=milestone_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return _format_milestone(db, milestone, settlement_id=settlement_ref.settlement_id)


@router.post("/milestones/{milestone_id}/request-revision", response_model=MilestoneReviewRead)
def request_revision_endpoint(
    milestone_id: int,
    payload: MilestoneRevisionRequest,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    review = deliverable_service.request_revision(
        db,
        ctx=ctx,
        milestone_id=milestone_id,
        deliverable_id=payload.deliverable_id,
        reason=payload.reason,
    )
    return MilestoneReviewRead(
        id=review.id,
        milestone_id=review.milestone_id,
        deliverable_id=review.deliverable_id,
        reviewed_by=review.reviewed_by,
        action=review.action,
        reason=review.reason,
        reviewed_at=review.reviewed_at,
    )
