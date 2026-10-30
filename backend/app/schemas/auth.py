"""Schema xác thực. Người phụ trách: TV1 (phần đăng ký doanh nghiệp phối hợp với TV4)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import CompanySize, UserRole, UserStatus, VerificationStatus
from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: str


class LogoutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ActivateAccountRequest(BaseModel):
    """Sinh viên kích hoạt tài khoản do trường cấp/import: token gửi qua email, đặt mật khẩu mới."""

    model_config = ConfigDict(str_strip_whitespace=True)

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class RegisterCompanyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)
    tax_code: str = Field(min_length=1, max_length=20)
    industry_id: Optional[int] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class StudentMeSummary(ORMModel):
    id: int
    student_code: str
    full_name: str
    class_name: Optional[str] = None
    faculty_id: int
    major_id: int
    cohort: str
    gpa: Optional[float] = None
    phone: Optional[str] = None


class CompanyMeSummary(ORMModel):
    id: int
    name: str
    tax_code: str
    industry_id: Optional[int] = None
    company_size: Optional[CompanySize] = None
    verification_status: VerificationStatus
    logo_url: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class AdminMeSummary(ORMModel):
    id: int
    full_name: str
    faculty_id: Optional[int] = None
    position: Optional[str] = None
    phone: Optional[str] = None


class MeResponse(ORMModel):
    id: int
    email: str
    role: UserRole
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime
    student: Optional[StudentMeSummary] = None
    company: Optional[CompanyMeSummary] = None
    admin: Optional[AdminMeSummary] = None


class RegisterCompanyResponse(BaseModel):
    user_id: int
    company_id: int
    email: str
    company_name: str
    tax_code: str
    status: UserStatus
    verification_status: VerificationStatus
    message: str
