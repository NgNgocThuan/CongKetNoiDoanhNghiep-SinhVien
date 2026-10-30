"""Thông báo trong ứng dụng. Người phụ trách: TV1."""
from typing import Optional

from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.notifications import (
    MarkAllReadResponse,
    NotificationRead,
    UnreadCountRead,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=Page[NotificationRead],
    summary="Danh sách thông báo của tôi",
)
def list_my_notifications(
    db: DbSession,
    user: CurrentUser,
    pagination: Pagination,
    is_read: Optional[bool] = None,
) -> dict:
    return notification_service.list_notifications(db, user, pagination, is_read=is_read)


@router.get(
    "/unread-count",
    response_model=UnreadCountRead,
    summary="Số lượng thông báo chưa đọc",
)
def get_unread_notification_count(
    user: CurrentUser,
    db: DbSession,
) -> UnreadCountRead:
    count = notification_service.unread_count(db, user)
    return UnreadCountRead(unread_count=count)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Đánh dấu đã đọc một thông báo",
)
def mark_notification_as_read(
    notification_id: int,
    user: CurrentUser,
    db: DbSession,
) -> NotificationRead:
    return notification_service.mark_read(db, user, notification_id)


@router.post(
    "/read-all",
    response_model=MarkAllReadResponse,
    summary="Đánh dấu tất cả thông báo là đã đọc",
)
def mark_all_notifications_as_read(
    user: CurrentUser,
    db: DbSession,
) -> MarkAllReadResponse:
    count = notification_service.mark_all_read(db, user)
    return MarkAllReadResponse(
        updated_count=count,
        message=f"Đã đánh dấu {count} thông báo là đã đọc",
    )
