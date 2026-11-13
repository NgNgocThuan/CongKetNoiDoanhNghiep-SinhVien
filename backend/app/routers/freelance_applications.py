from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, DbSession
from app.schemas.freelance_projects import ApplicationCreate, Resource, ResourcePage
from app.services import freelance_project_service as service
from app.services.freelancer_commands import run_command

router = APIRouter(tags=["Freelancer applications"])


@router.post(
    "/freelance-projects/{project_id}/applications",
    response_model=Resource,
    status_code=201,
    summary="Apply: /freelance-projects/{project_id}/applications",
)
def apply(project_id: int, payload: ApplicationCreate, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.apply_in_tx(db, user_id=u.id, project_id=project_id, payload=payload),
        )
    }


@router.get(
    "/freelance-projects/{project_id}/applications",
    response_model=ResourcePage,
    summary="Applications: /freelance-projects/{project_id}/applications",
)
def applications(
    project_id: int,
    db: DbSession,
    u: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return service.applications(db, user_id=u.id, project_id=project_id, number=page, size=size)


@router.get(
    "/freelance-applications/me",
    response_model=ResourcePage,
    summary="Mine: /freelance-applications/me",
)
def mine(
    db: DbSession, u: CurrentUser, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return service.applications(db, user_id=u.id, number=page, size=size)


@router.post(
    "/freelance-applications/{application_id}/withdraw",
    response_model=Resource,
    summary="Withdraw: /freelance-applications/{application_id}/withdraw",
)
def withdraw(application_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.application_action_in_tx(
                db, user_id=u.id, application_id=application_id, action="withdraw"
            ),
        )
    }


@router.post(
    "/freelance-applications/{application_id}/shortlist",
    response_model=Resource,
    summary="Shortlist: /freelance-applications/{application_id}/shortlist",
)
def shortlist(application_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.application_action_in_tx(
                db, user_id=u.id, application_id=application_id, action="shortlist"
            ),
        )
    }


@router.post(
    "/freelance-applications/{application_id}/reject",
    response_model=Resource,
    summary="Reject: /freelance-applications/{application_id}/reject",
)
def reject(application_id: int, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(
            db,
            lambda: service.application_action_in_tx(
                db, user_id=u.id, application_id=application_id, action="reject"
            ),
        )
    }
