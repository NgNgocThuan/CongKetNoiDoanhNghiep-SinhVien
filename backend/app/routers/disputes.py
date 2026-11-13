from fastapi import APIRouter, Header, Query

from app.dependencies import CurrentUser, DbSession
from app.schemas.freelance_projects import Resource, ResourcePage
from app.schemas.freelancer_disputes import DisputeCreate, EvidenceCreate, HashConfirm, Reason
from app.services import dispute_service as service
from app.services.freelancer_commands import run_command

router = APIRouter(tags=["Freelancer disputes"])


@router.post(
    "/milestones/{milestone_id}/disputes",
    response_model=Resource,
    status_code=201,
    summary="Create: /milestones/{milestone_id}/disputes",
)
def create(
    milestone_id: int,
    payload: DisputeCreate,
    db: DbSession,
    u: CurrentUser,
    key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
):
    return {
        "data": run_command(
            db,
            lambda: service.open_command_in_tx(
                db, user_id=u.id, milestone_id=milestone_id, payload=payload, key=key
            ),
        )
    }


@router.get(
    "/disputes/{dispute_id}", response_model=Resource, summary="Detail: /disputes/{dispute_id}"
)
def detail(dispute_id: int, db: DbSession, u: CurrentUser):
    return {"data": service.get_dispute(db, user_id=u.id, dispute_id=dispute_id)}


@router.post(
    "/disputes/{dispute_id}/evidence",
    response_model=Resource,
    status_code=201,
    summary="Evidence: /disputes/{dispute_id}/evidence",
)
def evidence(dispute_id: int, payload: EvidenceCreate, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.evidence_in_tx(
                db, user_id=u.id, dispute_id=dispute_id, payload=payload
            ),
        )
    }


@router.get(
    "/disputes/{dispute_id}/evidence",
    response_model=ResourcePage,
    summary="Evidence list: /disputes/{dispute_id}/evidence",
)
def evidence_list(
    dispute_id: int,
    db: DbSession,
    u: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return service.evidence_list(db, user_id=u.id, dispute_id=dispute_id, number=page, size=size)


@router.post(
    "/disputes/{dispute_id}/withdrawal",
    response_model=Resource,
    status_code=201,
    summary="Withdraw: /disputes/{dispute_id}/withdrawal",
)
def withdraw(dispute_id: int, payload: Reason, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.request_withdrawal_in_tx(
                db, user_id=u.id, dispute_id=dispute_id, reason=payload.reason
            ),
        )
    }


@router.post(
    "/disputes/{dispute_id}/withdrawal/confirm",
    response_model=Resource,
    summary="Confirm: /disputes/{dispute_id}/withdrawal/confirm",
)
def confirm(dispute_id: int, payload: HashConfirm, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.confirm_withdrawal_in_tx(
                db, user_id=u.id, dispute_id=dispute_id, content_hash=payload.content_hash
            ),
        )
    }
