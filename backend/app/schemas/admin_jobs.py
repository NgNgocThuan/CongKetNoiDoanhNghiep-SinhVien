"""Schema Pydantic: Kiểm duyệt tin tuyển dụng (admin). Người phụ trách: TV1."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import JobStatus, WorkMode
from app.schemas.common import ORMModel


class AdminJobRead(ORMModel):
    id: int
    company_id: int
    term_id: Optional[int] = None
    title: str
    position: str
    job_type_id: int
    industry_id: Optional[int] = None
    quantity: int
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    is_salary_negotiable: bool
    location: Optional[str] = None
    work_mode: WorkMode
    min_gpa: Optional[float] = None
    min_experience_months: Optional[int] = None
    deadline: date
    status: JobStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    view_count: int
    created_at: datetime
    updated_at: datetime


class AdminJobDetailRead(AdminJobRead):
    description: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    parsed_json: Optional[dict] = None
    parsed_at: Optional[datetime] = None


class JobRejectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reject_reason: str = Field(min_length=1, max_length=500, description="Lý do từ chối tin tuyển dụng")


class JobCloseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: Optional[str] = Field(default=None, max_length=500, description="Lý do đóng tin vi phạm")
