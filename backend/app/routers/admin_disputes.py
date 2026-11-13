from fastapi import APIRouter, Header, Query

from app.dependencies import AdminUser, DbSession
from app.schemas.freelance_projects import Resource, ResourcePage
from app.schemas.freelancer_disputes import (
    Assignment,
    DecisionCreate,
    EvidenceCreate,
    HoldCreate,
    Reason,
)
from app.services import dispute_service as service
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import ctx, milestone_scope
from app.services.milestone_hold_service import MilestoneHoldService

router = APIRouter(tags=["Freelancer dispute administration"])


@router.get("/admin/disputes", response_model=ResourcePage, summary="Listing: /admin/disputes")
def listing(
    db: DbSession, u: AdminUser, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return service.list_disputes(db, user_id=u.id, number=page, size=size)


@router.get(
    "/admin/disputes/{dispute_id}",
    response_model=Resource,
    summary="Detail: /admin/disputes/{dispute_id}",
)
def detail(dispute_id: int, db: DbSession, u: AdminUser):
    return {"data": service.get_dispute(db, user_id=u.id, dispute_id=dispute_id, is_admin=True)}


@router.get(
    "/admin/disputes/{dispute_id}/evidence",
    response_model=ResourcePage,
    summary="Evidence: /admin/disputes/{dispute_id}/evidence",
)
def evidence(
    dispute_id: int,
    db: DbSession,
    u: AdminUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return service.evidence_list(
        db, user_id=u.id, dispute_id=dispute_id, number=page, size=size, is_admin=True
    )


@router.post(
    "/admin/disputes/{dispute_id}/assign",
    response_model=Resource,
    summary="Assign: /admin/disputes/{dispute_id}/assign",
)
def assign(dispute_id: int, payload: Assignment, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: service.assign_in_tx(
                db, user_id=u.id, dispute_id=dispute_id, admin_id=payload.admin_id
            ),
        )
    }


@router.post(
    "/admin/disputes/{dispute_id}/decisions",
    response_model=Resource,
    status_code=201,
    summary="Decision: /admin/disputes/{dispute_id}/decisions",
)
def decision(
    dispute_id: int,
    payload: DecisionCreate,
    db: DbSession,
    u: AdminUser,
    key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
):
    return {
        "data": run_command(
            db,
            lambda: service.decision_command_in_tx(
                db, user_id=u.id, dispute_id=dispute_id, payload=payload, key=key
            ),
        )
    }


@router.post(
    "/admin/dispute-decisions/{decision_id}/execute",
    response_model=Resource,
    summary="Execute: /admin/dispute-decisions/{decision_id}/execute",
)
def execute(decision_id: int, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db, lambda: service.execute_decision_in_tx(db, user_id=u.id, decision_id=decision_id)
        )
    }


@router.post(
    "/admin/milestones/{milestone_id}/holds",
    response_model=Resource,
    status_code=201,
    summary="Hold: /admin/milestones/{milestone_id}/holds",
)
def hold(milestone_id: int, payload: HoldCreate, db: DbSession, u: AdminUser):
    def op():
        milestone_scope(db, milestone_id, u.id, allow_admin=True)
        if payload.reason_type != "ADMIN_REVIEW":
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Use the dispute/suspension workflow for this hold reason")
        hold_id = MilestoneHoldService().place_hold_in_tx(
            db,
            ctx=ctx(u.id),
            milestone_id=milestone_id,
            reason_type=payload.reason_type,
            reason_key="admin:" + payload.reason_key,
            dispute_id=None,
            note=payload.note,
        )
        return {"hold_id": str(hold_id)}

    return {"data": run_command(db, op)}


@router.post(
    "/admin/milestone-holds/{hold_id}/release",
    response_model=Resource,
    summary="Release: /admin/milestone-holds/{hold_id}/release",
)
def release(hold_id: int, payload: Reason, db: DbSession, u: AdminUser):
    run_command(
        db,
        lambda: MilestoneHoldService().release_hold_in_tx(
            db, ctx=ctx(u.id), hold_id=hold_id, note=payload.reason
        ),
    )
    return {"data": {"hold_id": str(hold_id), "released": True}}


@router.post(
    "/admin/dispute-decisions/{decision_id}/approve",
    response_model=Resource,
    summary="Approve: /admin/dispute-decisions/{decision_id}/approve",
)
def approve(decision_id: int, payload: Reason, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: service.approve_decision_in_tx(
                db, user_id=u.id, decision_id=decision_id, approve=True, reason=payload.reason
            ),
        )
    }


@router.post(
    "/admin/dispute-decisions/{decision_id}/reject",
    response_model=Resource,
    summary="Reject: /admin/dispute-decisions/{decision_id}/reject",
)
def reject(decision_id: int, payload: Reason, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: service.approve_decision_in_tx(
                db, user_id=u.id, decision_id=decision_id, approve=False, reason=payload.reason
            ),
        )
    }


@router.post(
    "/admin/disputes/{dispute_id}/late-evidence",
    response_model=Resource,
    status_code=201,
    summary="Record late evidence with a mandatory audit reason",
)
def late_evidence(
    dispute_id: int,
    payload: EvidenceCreate,
    db: DbSession,
    u: AdminUser,
    reason: str = Query(min_length=1, max_length=1000),
):
    return {
        "data": run_command(
            db,
            lambda: service.evidence_in_tx(
                db, user_id=u.id, dispute_id=dispute_id, payload=payload, late_reason=reason
            ),
        )
    }


@router.get(
    "/admin/disputes/{dispute_id}/decisions",
    response_model=ResourcePage,
    summary="Read immutable decision history",
)
def decisions(
    dispute_id: int,
    db: DbSession,
    u: AdminUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return service.decision_history(db, user_id=u.id, dispute_id=dispute_id, number=page, size=size)
