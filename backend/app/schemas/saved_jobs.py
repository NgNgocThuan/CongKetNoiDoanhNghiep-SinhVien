"""Response schemas for a student's saved jobs."""
from datetime import date, datetime
from typing import Optional

from app.core.enums import JobStatus, WorkMode
from app.schemas.common import ORMModel


class SavedJobCompanyBrief(ORMModel):
    id: int
    name: str
    logo_url: Optional[str] = None


class SavedJobTypeBrief(ORMModel):
    id: int
    code: str
    name: str


class SavedJobItem(ORMModel):
    """Mirrors TV4's JobListItem contract without owning the jobs module."""

    id: int
    title: str
    position: str
    term_id: Optional[int] = None
    location: Optional[str] = None
    work_mode: WorkMode
    quantity: int
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    is_salary_negotiable: bool
    deadline: date
    status: JobStatus
    created_at: datetime
    company: SavedJobCompanyBrief
    job_type: SavedJobTypeBrief


class SavedJobRead(ORMModel):
    saved_at: datetime
    job: SavedJobItem
