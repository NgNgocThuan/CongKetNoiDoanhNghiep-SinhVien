"""Schema xác thực. Người phụ trách: TV1 (phần đăng ký doanh nghiệp phối hợp với TV4)."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ActivateAccountRequest(BaseModel):
    """Sinh viên kích hoạt tài khoản do trường cấp/import: token gửi qua email, đặt mật khẩu mới."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class RegisterCompanyRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)
    tax_code: str = Field(min_length=1, max_length=20)
    industry_id: Optional[int] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
