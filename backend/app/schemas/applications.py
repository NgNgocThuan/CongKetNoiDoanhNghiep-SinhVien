"""Pydantic schemas for student applications."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ApplicationStatus
from app.schemas.common import ORMModel


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    job_id: int = Field(ge=1)
    cv_id: int = Field(ge=1)
    cover_letter: Optional[str] = Field(default=None, max_length=10000)
    invitation_id: Optional[int] = Field(default=None, ge=1)


class ApplicationCompanyBrief(ORMModel):
    id: int
    name: str
    logo_url: Optional[str] = None


class ApplicationJobBrief(ORMModel):
    id: int
    title: str
    position: str
    deadline: date
    company: ApplicationCompanyBrief


class ApplicationCVBrief(ORMModel):
    id: int
    title: str


class StatusLogRead(ORMModel):
    id: int
    old_status: Optional[ApplicationStatus] = None
    new_status: ApplicationStatus
    changed_by: Optional[int] = None
    note: Optional[str] = None
    changed_at: datetime


class ApplicationRead(ORMModel):
    id: int
    student_id: int
    job_id: int
    cv_id: int
    invitation_id: Optional[int] = None
    current_status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    job: ApplicationJobBrief


class ApplicationDetail(ApplicationRead):
    cv_snapshot_url: Optional[str] = None
    cover_letter: Optional[str] = None
    cv: ApplicationCVBrief
    status_logs: list[StatusLogRead] = Field(default_factory=list)
