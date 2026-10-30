"""Student application endpoints."""
from fastapi import APIRouter, BackgroundTasks

from app.core.enums import ApplicationStatus
from app.dependencies import CurrentStudent, DbSession, Pagination
from app.schemas.applications import ApplicationCreate, ApplicationDetail, ApplicationRead
from app.schemas.common import Page
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationDetail, status_code=201, summary="Nộp đơn ứng tuyển")
def apply(
    data: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: DbSession,
    student: CurrentStudent,
):
    created = application_service.apply(db, background_tasks, student, data)
    # Tải lại đầy đủ quan hệ để response khớp tài liệu Swagger.
    return application_service.get_my_application(db, student, created.id)


@router.get("/me", response_model=Page[ApplicationRead], summary="Danh sách đơn của tôi")
def list_my_applications(
    db: DbSession,
    student: CurrentStudent,
    pagination: Pagination,
    status: ApplicationStatus | None = None,
):
    return application_service.list_my_applications(
        db, student, pagination, status=status
    )


@router.get(
    "/{application_id}", response_model=ApplicationDetail, summary="Chi tiết đơn ứng tuyển"
)
def get_my_application(application_id: int, db: DbSession, student: CurrentStudent):
    return application_service.get_my_application(db, student, application_id)


@router.post(
    "/{application_id}/withdraw",
    response_model=ApplicationDetail,
    summary="Rút đơn ứng tuyển",
)
def withdraw(application_id: int, db: DbSession, student: CurrentStudent):
    return application_service.withdraw(db, student, application_id)
