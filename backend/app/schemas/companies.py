"""Schema Pydantic: Hồ sơ doanh nghiệp. Người phụ trách: Đỗ Hồng Khôi."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CompanyDocType, CompanySize, VerificationStatus
from app.schemas.common import ORMModel


class CompanyUpdate(BaseModel):
    """Doanh nghiệp tự cập nhật. Không cho sửa tên, mã số thuế (đã được trường xác thực)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    industry_id: Optional[int] = Field(default=None, ge=1)
    company_size: Optional[CompanySize] = None
    address: Optional[str] = Field(default=None, max_length=500)
    website: Optional[str] = Field(default=None, max_length=255, examples=["https://congty.vn"])
    logo_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    tech_stack: Optional[str] = Field(default=None, max_length=500, examples=["Python, FastAPI, MySQL"])
    benefits: Optional[str] = None
    contact_name: Optional[str] = Field(default=None, max_length=255)
    contact_phone: Optional[str] = Field(default=None, max_length=20)


class CompanyDocumentRead(ORMModel):
    id: int
    doc_type: CompanyDocType
    file_url: str
    uploaded_at: datetime


class CompanyRead(ORMModel):
    """Hồ sơ đầy đủ, chỉ chính doanh nghiệp xem được."""

    id: int
    name: str
    tax_code: str
    industry_id: Optional[int] = None
    company_size: Optional[CompanySize] = None
    address: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    benefits: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    verification_status: VerificationStatus
    verified_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    documents: list[CompanyDocumentRead] = []


class CompanyPublicRead(ORMModel):
    """Hồ sơ công khai cho sinh viên: không có mã số thuế, SĐT liên hệ, giấy tờ, trạng thái xác thực."""

    id: int
    name: str
    industry_id: Optional[int] = None
    company_size: Optional[CompanySize] = None
    address: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    benefits: Optional[str] = None