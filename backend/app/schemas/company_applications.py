"""Responses for employer-owned applications; privacy is enforced by the service."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ApplicationStatus
from app.schemas.applications import StatusLogRead
from app.schemas.common import ORMModel


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: str | None = Field(None, max_length=500)


class StudentInfoNested(ORMModel):
    id: int
    full_name: str
    gpa: float | None = None
    experience_months: int = 0
    skills: list[str] = Field(default_factory=list)


class CompanyApplicationRead(ORMModel):
    id: int
    job_id: int
    student_id: int
    cv_id: int
    current_status: ApplicationStatus
    cover_letter: str | None = None
    applied_at: datetime
    updated_at: datetime
    contact_email: str | None = None
    contact_phone: str | None = None
    student: StudentInfoNested
    status_logs: list[StatusLogRead] = Field(default_factory=list)
    cv_snapshot_url: str | None = None
    cv_download_url: str


class CompanyApplicationDetail(CompanyApplicationRead):
    pass
