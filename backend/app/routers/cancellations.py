from fastapi import APIRouter, Header

from app.dependencies import CurrentUser, DbSession
from app.schemas.freelance_projects import Resource
from app.schemas.freelancer_disputes import CancellationCreate, HashConfirm
from app.services import cancellation_service as service
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import record

router = APIRouter(tags=["Freelancer cancellations"])


@router.post(
    "/milestones/{milestone_id}/cancellations",
    response_model=Resource,
    status_code=201,
    summary="Create: /milestones/{milestone_id}/cancellations",
)
def create(
    milestone_id: int,
    payload: CancellationCreate,
    db: DbSession,
    u: CurrentUser,
    key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
):
    return {
        "data": run_command(
            db,
            lambda: service.propose_command_in_tx(
                db, user_id=u.id, milestone_id=milestone_id, payload=payload, key=key
            ),
        )
    }


@router.get(
    "/cancellations/{cancellation_id}",
    response_model=Resource,
    summary="Detail: /cancellations/{cancellation_id}",
)
def detail(cancellation_id: int, db: DbSession, u: CurrentUser):
    return {"data": record(service.scope(db, cancellation_id, u.id)[-1])}


@router.post(
    "/cancellations/{cancellation_id}/accept",
    response_model=Resource,
    summary="Accept: /cancellations/{cancellation_id}/accept",
)
def accept(cancellation_id: int, payload: HashConfirm, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.action_in_tx(
                db,
                user_id=u.id,
                cancellation_id=cancellation_id,
                action="accept",
                content_hash=payload.content_hash,
            ),
        )
    }


@router.post(
    "/cancellations/{cancellation_id}/execute",
    response_model=Resource,
    summary="Execute: /cancellations/{cancellation_id}/execute",
)
def execute(cancellation_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db, lambda: service.execute_in_tx(db, user_id=u.id, cancellation_id=cancellation_id)
        )
    }


@router.post(
    "/cancellations/{cancellation_id}/reject",
    response_model=Resource,
    summary="Reject: /cancellations/{cancellation_id}/reject",
)
def reject(cancellation_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.action_in_tx(
                db, user_id=u.id, cancellation_id=cancellation_id, action="reject"
            ),
        )
    }


@router.post(
    "/cancellations/{cancellation_id}/withdraw",
    response_model=Resource,
    summary="Withdraw: /cancellations/{cancellation_id}/withdraw",
)
def withdraw(cancellation_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.action_in_tx(
                db, user_id=u.id, cancellation_id=cancellation_id, action="withdraw"
            ),
        )
    }
