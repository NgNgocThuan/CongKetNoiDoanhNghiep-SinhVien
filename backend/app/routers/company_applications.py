"""Quản lý ứng viên (Kanban). Người phụ trách: Khôi."""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Query

from app.core.enums import ApplicationStatus
from app.dependencies import CurrentCompany, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.applications import ApplicationRead, ApplicationDetail, ApplicationStatusUpdate, StatusLogRead
from app.services import company_application_service

router = APIRouter(prefix="/company/applications", tags=["Company - Applications"])


@router.get("", response_model=Page[ApplicationRead], summary="Danh sách đơn theo job_id và bộ lọc")
def list_applications(
    db: DbSession,
    company: CurrentCompany,
    pagination: Pagination,
    job_id: int = Query(..., description="ID tin tuyển dụng"),
    status: Optional[ApplicationStatus] = None,
    major_id: Optional[int] = None,
    min_gpa: Optional[float] = None,
    skill_id: Optional[int] = None,
    min_experience_months: Optional[int] = None,
):
    return company_application_service.list_applications(
        db, company, job_id, pagination, status=status, major_id=major_id,
        min_gpa=min_gpa, skill_id=skill_id, min_experience_months=min_experience_months
    )


@router.get("/{application_id}", response_model=ApplicationDetail, summary="Xem chi tiết đơn + CV snapshot")
def get_application(application_id: int, db: DbSession, company: CurrentCompany):
    return company_application_service.get_application(db, company, application_id)


@router.put("/{application_id}/status", response_model=ApplicationRead, summary="Đổi trạng thái đơn (Kanban)")
def change_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    db: DbSession,
    company: CurrentCompany,
    background_tasks: BackgroundTasks,
):
    return company_application_service.log_status_change(
        db, background_tasks, company, application_id, data.status, data.note
    )


@router.get("/{application_id}/history", response_model=list[StatusLogRead], summary="Lịch sử xử lý đơn")
def get_history(application_id: int, db: DbSession, company: CurrentCompany):
    return company_application_service.get_history(db, company, application_id)