"""Schema Pydantic: Kiểm duyệt doanh nghiệp (admin). Người phụ trách: TV1."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CompanyDocType, CompanySize, VerificationStatus
from app.schemas.common import ORMModel


class CompanyDocumentAdminRead(ORMModel):
    id: int
    doc_type: CompanyDocType
    file_url: str
    uploaded_at: datetime


class AdminCompanyRead(ORMModel):
    id: int
    user_id: int
    name: str
    tax_code: str
    industry_id: Optional[int] = None
    company_size: Optional[CompanySize] = None
    address: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    verification_status: VerificationStatus
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminCompanyDetailRead(AdminCompanyRead):
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    benefits: Optional[str] = None
    documents: list[CompanyDocumentAdminRead] = []


class CompanyRejectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reject_reason: str = Field(min_length=1, max_length=500, description="Lý do từ chối hồ sơ doanh nghiệp")
