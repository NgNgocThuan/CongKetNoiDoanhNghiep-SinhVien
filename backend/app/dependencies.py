"""Dependency dùng chung cho routers: session DB, xác thực, phân quyền, phân trang.

Cách dùng trong router:

    @router.get("/me")
    def me(student: CurrentStudent): ...

    @router.post("/")
    def create(data: Schema, db: DbSession, admin: AdminUser): ...
"""
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.models import Company, Student, User
from app.schemas.common import PageParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    payload = decode_token(token, expected_type="access")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Tài khoản không tồn tại")
    if user.status == UserStatus.LOCKED:
        raise ForbiddenError("Tài khoản đã bị khóa", code="ACCOUNT_LOCKED")
    if user.status != UserStatus.ACTIVE:
        raise ForbiddenError("Tài khoản chưa được kích hoạt hoặc chưa được duyệt", code="ACCOUNT_NOT_ACTIVE")
    return user


def require_roles(*roles: UserRole):
    """Tạo dependency chỉ cho phép các role chỉ định."""

    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise ForbiddenError("Bạn không có quyền thực hiện thao tác này")
        return user

    return checker


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]
CompanyUser = Annotated[User, Depends(require_roles(UserRole.COMPANY))]


def get_current_student(user: StudentUser) -> Student:
    if user.student is None:
        raise NotFoundError("Tài khoản chưa có hồ sơ sinh viên")
    return user.student


def get_current_company(user: CompanyUser) -> Company:
    if user.company is None:
        raise NotFoundError("Tài khoản chưa có hồ sơ doanh nghiệp")
    return user.company


CurrentStudent = Annotated[Student, Depends(get_current_student)]
CurrentCompany = Annotated[Company, Depends(get_current_company)]


def pagination_params(
    page: int = Query(1, ge=1, description="Trang, bắt đầu từ 1"),
    size: int = Query(20, ge=1, le=100, description="Số dòng mỗi trang"),
) -> PageParams:
    return PageParams(page=page, size=size)


Pagination = Annotated[PageParams, Depends(pagination_params)]
