"""Báo cáo vi phạm. Người phụ trách: TV1."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, status

from app.core.enums import ReportStatus, ReportTargetType
from app.dependencies import AdminUser, CurrentUser, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.reports import ReportCreate, ReportHandle, ReportRead
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Gửi báo cáo vi phạm mới (User)",
)
def create_report(
    data: ReportCreate,
    user: CurrentUser,
    db: DbSession,
) -> ReportRead:
    return report_service.create_report(db, user, data)


@router.get(
    "",
    response_model=Page[ReportRead],
    summary="Danh sách báo cáo vi phạm (Admin)",
)
def list_reports(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    status: Optional[ReportStatus] = None,
    target_type: Optional[ReportTargetType] = None,
) -> dict:
    return report_service.list_reports(
        db, pagination, status=status, target_type=target_type
    )


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    summary="Chi tiết báo cáo vi phạm (Admin)",
)
def get_report(
    report_id: int,
    db: DbSession,
    _: AdminUser,
) -> ReportRead:
    return report_service.get_report(db, report_id)


@router.post(
    "/{report_id}/handle",
    response_model=ReportRead,
    summary="Xử lý báo cáo vi phạm (Admin)",
)
def handle_report(
    report_id: int,
    data: ReportHandle,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> ReportRead:
    return report_service.handle_report(
        db,
        report_id,
        admin,
        data,
        background_tasks=background_tasks,
    )
