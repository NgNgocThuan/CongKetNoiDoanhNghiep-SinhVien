"""Quản lý tài khoản (admin). Người phụ trách: TV1."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, status

from app.core.enums import EmailStatus, UserRole, UserStatus
from app.dependencies import AdminUser, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.users import (
    AdminCreate,
    EmailLogRead,
    LockUserRequest,
    RetryEmailsResponse,
    UserRead,
)
from app.services import email_service, user_service

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])


@router.get(
    "",
    response_model=Page[UserRead],
    summary="Danh sách tài khoản người dùng",
)
def list_users(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    q: Optional[str] = None,
) -> dict:
    return user_service.list_users(db, pagination, role=role, status=status, q=q)




@router.get(
    "/email-logs",
    response_model=Page[EmailLogRead],
    summary="Danh sách nhật ký gửi email hệ thống",
)
def list_email_logs(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    status: Optional[EmailStatus] = None,
    type: Optional[str] = None,
) -> dict:
    return email_service.list_email_logs(db, pagination, status=status, type=type)


@router.post(
    "/email-logs/retry",
    response_model=RetryEmailsResponse,
    summary="Thử gửi lại các email bị lỗi (FAILED)",
)
def retry_failed_emails(
    db: DbSession,
    _: AdminUser,
    background_tasks: BackgroundTasks,
) -> RetryEmailsResponse:
    count = email_service.retry_failed_emails(db, background_tasks)
    return RetryEmailsResponse(
        retried_count=count,
        message=f"Đã đưa {count} email lỗi vào hàng đợi gửi lại",
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Chi tiết tài khoản người dùng",
)
def get_user_detail(
    user_id: int,
    db: DbSession,
    _: AdminUser,
) -> UserRead:
    return user_service.get_user(db, user_id)


@router.post(
    "/{user_id}/lock",
    response_model=UserRead,
    summary="Khóa tài khoản người dùng (bắt buộc nhập lý do)",
)
def lock_user(
    user_id: int,
    data: LockUserRequest,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> UserRead:
    return user_service.lock_user(
        db,
        user_id,
        data,
        current_admin=admin,
        background_tasks=background_tasks,
    )


@router.post(
    "/{user_id}/unlock",
    response_model=UserRead,
    summary="Mở khóa tài khoản người dùng",
)
def unlock_user(
    user_id: int,
    _: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> UserRead:
    return user_service.unlock_user(db, user_id, background_tasks=background_tasks)


@router.post(
    "/admins",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo tài khoản quản trị viên mới",
)
def create_admin_user(
    data: AdminCreate,
    _: AdminUser,
    db: DbSession,
) -> UserRead:
    return user_service.create_admin(db, data)
