"""Xác thực & phiên đăng nhập. Người phụ trách: TV1."""
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, status
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import CurrentUser, DbSession, oauth2_scheme
from app.schemas.auth import (
    ActivateAccountRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RegisterCompanyRequest,
    RegisterCompanyResponse,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.common import Message
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.put("/me/avatar", response_model=Message, summary="Tải ảnh đại diện từ thiết bị")
async def upload_avatar(file: UploadFile, user: CurrentUser, db: DbSession):
    from app.models import UserAvatar
    from app.services.avatar_service import MAX_BYTES, normalize_avatar

    data = normalize_avatar(await file.read(MAX_BYTES + 1))
    avatar = db.get(UserAvatar, user.id)
    if avatar:
        avatar.image = data
    else:
        db.add(UserAvatar(user_id=user.id, image=data))
    db.commit()
    return Message(message="Đã cập nhật ảnh đại diện")


@router.get("/users/{user_id}/avatar", summary="Xem ảnh đại diện người dùng")
def get_avatar(user_id: int, _: CurrentUser, db: DbSession):
    from app.models import UserAvatar

    avatar = db.get(UserAvatar, user_id)
    if not avatar:
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
    return Response(avatar.image, media_type="image/jpeg", headers={"Cache-Control": "private, no-store"})


@router.post(
    "/token",
    response_model=TokenPair,
    summary="Đăng nhập OAuth2 Form (cho nút Authorize Swagger)",
)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenPair:
    return auth_service.login(db, email=form_data.username, password=form_data.password)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Đăng nhập hệ thống (JSON)",
)
def login(
    data: LoginRequest,
    db: DbSession,
) -> TokenPair:
    return auth_service.login(db, email=data.email, password=data.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Làm mới token đăng nhập",
)
def refresh_tokens(
    data: RefreshRequest,
    db: DbSession,
) -> TokenPair:
    return auth_service.refresh_tokens(db, refresh_token=data.refresh_token)


@router.post(
    "/logout",
    response_model=Message,
    summary="Đăng xuất",
)
def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    _: CurrentUser,
    db: DbSession,
    data: Optional[LogoutRequest] = None,
) -> Message:
    auth_service.logout(token, data.refresh_token if data else None, db=db)
    return Message(message="Đăng xuất thành công")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Xem thông tin tài khoản hiện tại",
)
def get_current_user_profile(
    user: CurrentUser,
    db: DbSession,
) -> MeResponse:
    return auth_service.get_me(db, user)


@router.post(
    "/change-password",
    response_model=Message,
    summary="Đổi mật khẩu tài khoản hiện tại",
)
def change_password(
    data: ChangePasswordRequest,
    user: CurrentUser,
    db: DbSession,
) -> Message:
    auth_service.change_password(db, user, data)
    return Message(message="Đổi mật khẩu thành công")


@router.post(
    "/forgot-password",
    response_model=Message,
    summary="Yêu cầu đặt lại mật khẩu qua email",
)
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> Message:
    auth_service.request_password_reset(db, background_tasks, data.email)
    return Message(message="Nếu tài khoản đủ điều kiện, yêu cầu gửi hướng dẫn đặt lại mật khẩu đã được ghi nhận. Vui lòng kiểm tra hộp thư và thư rác.")


@router.post(
    "/reset-password",
    response_model=Message,
    summary="Đặt lại mật khẩu bằng mã token",
)
def reset_password(
    data: ResetPasswordRequest,
    db: DbSession,
) -> Message:
    auth_service.reset_password(db, data)
    return Message(message="Đặt lại mật khẩu thành công")


@router.post(
    "/activate",
    response_model=Message,
    summary="Kích hoạt tài khoản sinh viên trường cấp",
)
def activate_account(
    data: ActivateAccountRequest,
    db: DbSession,
) -> Message:
    auth_service.activate_student_account(db, data)
    return Message(message="Kích hoạt tài khoản sinh viên thành công")


@router.post(
    "/register-company",
    response_model=RegisterCompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Doanh nghiệp đăng ký tài khoản (chờ phê duyệt)",
)
def register_company(
    data: RegisterCompanyRequest,
    db: DbSession,
) -> RegisterCompanyResponse:
    return auth_service.register_company(db, data)
