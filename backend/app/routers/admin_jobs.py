"""Nhà trường: kiểm duyệt tin tuyển dụng. Người phụ trách: TV1."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from app.core.enums import JobStatus
from app.dependencies import AdminUser, DbSession, Pagination
from app.schemas.admin_jobs import (
    AdminJobDetailRead,
    AdminJobRead,
    JobCloseRequest,
    JobRejectRequest,
)
from app.schemas.common import Page
from app.services import admin_job_service

router = APIRouter(prefix="/admin/jobs", tags=["Admin - Jobs"])


@router.get(
    "",
    response_model=Page[AdminJobRead],
    summary="Danh sách tin tuyển dụng kiểm duyệt (Admin)",
)
def list_jobs(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    status: Optional[JobStatus] = JobStatus.PENDING_APPROVAL,
    company_id: Optional[int] = None,
    term_id: Optional[int] = None,
    q: Optional[str] = None,
) -> dict:
    return admin_job_service.list_jobs(
        db,
        pagination,
        status=status,
        company_id=company_id,
        term_id=term_id,
        q=q,
    )


@router.get(
    "/{job_id}",
    response_model=AdminJobDetailRead,
    summary="Chi tiết tin tuyển dụng (Admin)",
)
def get_job_detail(
    job_id: int,
    db: DbSession,
    _: AdminUser,
) -> AdminJobDetailRead:
    return admin_job_service.get_job(db, job_id)


@router.post(
    "/{job_id}/approve",
    response_model=AdminJobDetailRead,
    summary="Phê duyệt tin tuyển dụng (Admin)",
)
def approve_job(
    job_id: int,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> AdminJobDetailRead:
    return admin_job_service.approve_job(
        db, job_id, admin, background_tasks=background_tasks
    )


@router.post(
    "/{job_id}/reject",
    response_model=AdminJobDetailRead,
    summary="Từ chối phê duyệt tin tuyển dụng (Admin - bắt buộc lý do)",
)
def reject_job(
    job_id: int,
    data: JobRejectRequest,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> AdminJobDetailRead:
    return admin_job_service.reject_job(
        db, job_id, admin, data, background_tasks=background_tasks
    )


@router.post(
    "/{job_id}/close",
    response_model=AdminJobDetailRead,
    summary="Đóng tin tuyển dụng vi phạm (Admin)",
)
def close_job(
    job_id: int,
    admin: AdminUser,
    db: DbSession,
    data: Optional[JobCloseRequest] = None,
) -> AdminJobDetailRead:
    reason = data.reason if data is not None else None
    return admin_job_service.close_job(db, job_id, admin, reason=reason)
