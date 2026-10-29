"""Schema Pydantic: Lời mời ứng tuyển. Người phụ trách: Khôi."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import InvitationStatus
from app.schemas.common import ORMModel


class InvitationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_id: int = Field(ge=1)
    student_id: int = Field(ge=1)
    message: Optional[str] = Field(default=None, max_length=500)


class InvitationRead(ORMModel):
    id: int
    job_id: int
    student_id: int
    company_id: int
    status: str
    message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None  # Cho phép None nếu model DB không có cột này
    
    model_config = ConfigDict(from_attributes=True)