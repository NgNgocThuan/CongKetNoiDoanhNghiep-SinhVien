from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OtpRequestSchema(BaseModel):
    identifier: str = Field(..., description="Email hoặc số điện thoại nhận OTP")
    purpose: str = Field(..., description="Ngữ cảnh sử dụng OTP (register, verify_company, ...)")


class OtpVerifySchema(BaseModel):
    identifier: str
    purpose: str
    code: str = Field(..., min_length=6, max_length=6, description="Mã OTP 6 chữ số")


class CompanyVerificationSubmitSchema(BaseModel):
    tax_code: str = Field(..., min_length=10, max_length=14, description="Mã số thuế doanh nghiệp")
    company_name: str = Field(..., description="Tên đầy đủ của doanh nghiệp")
    business_license_url: Optional[str] = Field(None, description="Đường dẫn file giấy phép kinh doanh")


class MouAgreementSchema(BaseModel):
    company_id: int
    effective_from: datetime
    effective_until: datetime
    mou_code: str = Field(..., description="Mã biên bản ghi nhớ MOU")