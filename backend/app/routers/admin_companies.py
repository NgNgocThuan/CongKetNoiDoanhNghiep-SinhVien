"""Nhà trường: kiểm duyệt doanh nghiệp. Người phụ trách: TV1."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from app.core.enums import VerificationStatus
from app.dependencies import AdminUser, DbSession, Pagination
from app.schemas.admin_companies import (
    AdminCompanyDetailRead,
    AdminCompanyRead,
    CompanyRejectRequest,
)
from app.schemas.common import Page
from app.services import admin_company_service

router = APIRouter(prefix="/admin/companies", tags=["Admin - Companies"])


@router.get(
    "",
    response_model=Page[AdminCompanyRead],
    summary="Danh sách doanh nghiệp chờ duyệt hoặc theo trạng thái (Admin)",
)
def list_companies(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    verification_status: Optional[VerificationStatus] = None,
    q: Optional[str] = None,
) -> dict:
    return admin_company_service.list_companies(
        db, pagination, verification_status=verification_status, q=q
    )


@router.get(
    "/{company_id}",
    response_model=AdminCompanyDetailRead,
    summary="Chi tiết doanh nghiệp kèm giấy tờ xác thực (Admin)",
)
def get_company_detail(
    company_id: int,
    db: DbSession,
    _: AdminUser,
) -> AdminCompanyDetailRead:
    return admin_company_service.get_company_detail(db, company_id)


@router.post(
    "/{company_id}/approve",
    response_model=AdminCompanyDetailRead,
    summary="Phê duyệt doanh nghiệp (Admin)",
)
def approve_company(
    company_id: int,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> AdminCompanyDetailRead:
    return admin_company_service.approve_company(
        db, company_id, admin, background_tasks=background_tasks
    )


@router.post(
    "/{company_id}/reject",
    response_model=AdminCompanyDetailRead,
    summary="Từ chối phê duyệt doanh nghiệp (Admin - bắt buộc lý do)",
)
def reject_company(
    company_id: int,
    data: CompanyRejectRequest,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> AdminCompanyDetailRead:
    return admin_company_service.reject_company(
        db, company_id, admin, data, background_tasks=background_tasks
    )
