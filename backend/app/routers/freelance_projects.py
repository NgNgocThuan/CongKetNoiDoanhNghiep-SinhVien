from fastapi import APIRouter, Header, Query

from app.dependencies import AdminUser, CurrentUser, DbSession
from app.schemas.freelance_projects import (
    BudgetUpdate,
    Expansion,
    ProjectCreate,
    Resource,
    ResourcePage,
    ReviewInput,
    SelectStudent,
)
from app.services import freelance_project_service as service
from app.services.freelancer_commands import run_command

router = APIRouter(tags=["Freelancer projects"])


@router.get(
    "/freelance-projects", response_model=ResourcePage, summary="Projects: /freelance-projects"
)
def projects(
    db: DbSession,
    u: CurrentUser,
    mine: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=30),
):
    return service.list_projects(
        db, user_id=u.id, mine=mine, number=page, size=size, search=q, category=category
    )


@router.post(
    "/freelance-projects",
    response_model=Resource,
    status_code=201,
    summary="Create: /freelance-projects",
)
def create(payload: ProjectCreate, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(db, lambda: service.create_in_tx(db, user_id=u.id, payload=payload))
    }


@router.get(
    "/freelance-projects/{project_id}",
    response_model=Resource,
    summary="Detail: /freelance-projects/{project_id}",
)
def detail(project_id: int, db: DbSession, u: CurrentUser):
    return {"data": service.get_project(db, user_id=u.id, project_id=project_id)}


@router.patch(
    "/freelance-projects/{project_id}",
    response_model=Resource,
    summary="Update: /freelance-projects/{project_id}",
)
def update(project_id: int, payload: ProjectCreate, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.update_in_tx(db, user_id=u.id, project_id=project_id, payload=payload),
        )
    }


@router.post(
    "/freelance-projects/{project_id}/submit",
    response_model=Resource,
    summary="Submit: /freelance-projects/{project_id}/submit",
)
def submit(project_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db, lambda: service.submit_in_tx(db, user_id=u.id, project_id=project_id)
        )
    }


@router.post(
    "/freelance-projects/{project_id}/select",
    response_model=Resource,
    summary="Select student: /freelance-projects/{project_id}/select",
)
def select_student(
    project_id: int,
    payload: SelectStudent,
    db: DbSession,
    u: CurrentUser,
    key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
):
    return {
        "data": run_command(
            db,
            lambda: service.select_in_tx(
                db, user_id=u.id, project_id=project_id, payload=payload, key=key
            ),
        )
    }


@router.patch(
    "/freelance-contracts/{contract_id}/budget",
    response_model=Resource,
    summary="Budget: /freelance-contracts/{contract_id}/budget",
)
def budget(contract_id: int, payload: BudgetUpdate, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.budget_in_tx(
                db, user_id=u.id, contract_id=contract_id, amount=payload.allocated_amount
            ),
        )
    }


@router.post(
    "/freelance-projects/{project_id}/expansions",
    response_model=Resource,
    status_code=201,
    summary="Expand: /freelance-projects/{project_id}/expansions",
)
def expand(
    project_id: int,
    payload: Expansion,
    db: DbSession,
    u: CurrentUser,
    key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
):
    return {
        "data": run_command(
            db,
            lambda: service.expand_in_tx(
                db, user_id=u.id, project_id=project_id, payload=payload, key=key
            ),
        )
    }


@router.post(
    "/freelance-projects/{project_id}/close-recruitment",
    response_model=Resource,
    summary="close-recruitment",
)
def close_recruitment(project_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.recruitment_in_tx(
                db, user_id=u.id, project_id=project_id, reopen=False
            ),
        )
    }


@router.post(
    "/freelance-projects/{project_id}/reopen-recruitment",
    response_model=Resource,
    summary="reopen-recruitment",
)
def reopen_recruitment(project_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.recruitment_in_tx(db, user_id=u.id, project_id=project_id, reopen=True),
        )
    }


@router.post(
    "/admin/freelance-projects/{project_id}/approve",
    response_model=Resource,
    summary="Admin approve: /admin/freelance-projects/{project_id}/approve",
)
def admin_approve(project_id: int, payload: ReviewInput, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: service.review_in_tx(
                db, user_id=u.id, project_id=project_id, decision="APPROVED", reason=payload.reason
            ),
        )
    }


@router.post(
    "/admin/freelance-projects/{project_id}/reject",
    response_model=Resource,
    summary="Admin reject: /admin/freelance-projects/{project_id}/reject",
)
def admin_reject(project_id: int, payload: ReviewInput, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: service.review_in_tx(
                db, user_id=u.id, project_id=project_id, decision="REJECTED", reason=payload.reason
            ),
        )
    }


@router.post(
    "/admin/freelance-projects/{project_id}/request-revision",
    response_model=Resource,
    summary="Admin request revision: /admin/freelance-projects/{project_id}/request-revision",
)
def admin_request_revision(project_id: int, payload: ReviewInput, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: service.review_in_tx(
                db,
                user_id=u.id,
                project_id=project_id,
                decision="NEEDS_REVISION",
                reason=payload.reason,
            ),
        )
    }


@router.post(
    "/admin/freelance-projects/{project_id}/expansions/{request_key}/approve",
    response_model=Resource,
    summary="Expansion approve: /admin/freelance-projects/{project_id}/expansions/{request_key}/approve",
)
def expansion_approve(
    project_id: int, request_key: str, payload: ReviewInput, db: DbSession, u: AdminUser
):
    return {
        "data": run_command(
            db,
            lambda: service.decide_expansion_in_tx(
                db,
                user_id=u.id,
                project_id=project_id,
                request_key=request_key,
                approve=True,
                reason=payload.reason,
            ),
        )
    }


@router.post(
    "/admin/freelance-projects/{project_id}/expansions/{request_key}/reject",
    response_model=Resource,
    summary="Expansion reject: /admin/freelance-projects/{project_id}/expansions/{request_key}/reject",
)
def expansion_reject(
    project_id: int, request_key: str, payload: ReviewInput, db: DbSession, u: AdminUser
):
    return {
        "data": run_command(
            db,
            lambda: service.decide_expansion_in_tx(
                db,
                user_id=u.id,
                project_id=project_id,
                request_key=request_key,
                approve=False,
                reason=payload.reason,
            ),
        )
    }


@router.get(
    "/freelance-projects/{project_id}/contracts",
    response_model=ResourcePage,
    summary="List own contracts within a project",
)
def project_contracts(
    project_id: int,
    db: DbSession,
    u: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return service.contracts(db, user_id=u.id, project_id=project_id, number=page, size=size)


@router.get(
    "/freelance-projects/{project_id}/budget",
    response_model=Resource,
    summary="Project budget allocations, not escrow funds",
)
def project_budget(project_id: int, db: DbSession, u: CurrentUser):
    return {"data": service.summary(db, user_id=u.id, project_id=project_id)}


@router.post(
    "/freelance-projects/{project_id}/close",
    response_model=Resource,
    summary="Recompute project closure after all obligations",
)
def close(project_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db, lambda: service.close_in_tx(db, user_id=u.id, project_id=project_id)
        )
    }


@router.post(
    "/freelance-projects/{project_id}/cancel",
    response_model=Resource,
    summary="Cancel project without unresolved obligations",
)
def cancel(project_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db, lambda: service.close_in_tx(db, user_id=u.id, project_id=project_id, cancel=True)
        )
    }


@router.post(
    "/freelance-contracts/{contract_id}/cancel-draft",
    response_model=Resource,
    summary="Cancel draft contract and release reserved allocation",
)
def cancel_draft(contract_id: int, payload: ReviewInput, db: DbSession, u: CurrentUser):
    from app.services.freelance_closure_service import FreelanceClosureService
    from app.services.freelancer_domain import ctx

    run_command(
        db,
        lambda: FreelanceClosureService().cancel_draft_contract_in_tx(
            db, ctx=ctx(u.id), contract_id=contract_id, reason=payload.reason
        ),
    )
    return {"data": {"contract_id": str(contract_id), "status": "CANCELLED"}}
