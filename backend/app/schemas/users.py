"""Schema Pydantic: Quản lý tài khoản (admin). Người phụ trách: TV1."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import EmailStatus, UserRole, UserStatus
from app.schemas.common import ORMModel


class AdminProfileRead(ORMModel):
    id: int
    full_name: str
    faculty_id: Optional[int] = None
    position: Optional[str] = None
    phone: Optional[str] = None


class UserRead(ORMModel):
    id: int
    email: str
    role: UserRole
    status: UserStatus
    locked_reason: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    admin: Optional[AdminProfileRead] = None


class UserFilter(BaseModel):
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    q: Optional[str] = None


class LockUserRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=1, max_length=500, description="Lý do khóa tài khoản")


class AdminCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    faculty_id: Optional[int] = None
    position: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)



class EmailLogRead(ORMModel):
    id: int
    user_id: Optional[int] = None
    recipient_email: str
    type: str
    subject: str
    status: EmailStatus
    error_message: Optional[str] = None
    retry_count: int
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class RetryEmailsResponse(BaseModel):
    retried_count: int
    message: str
