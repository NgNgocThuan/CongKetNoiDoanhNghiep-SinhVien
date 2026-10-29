"""Schema Pydantic: Tin tuyển dụng. Người phụ trách: Khôi.

Phân cấp schema response (TV3 dùng JobListItem/JobRead cho "việc làm yêu thích"):
  JobListItem  -> thẻ tin trong danh sách (kèm company + job_type rút gọn)
  JobMyItem    -> JobListItem + view_count, application_count (danh sách tin của doanh nghiệp)
  JobRead      -> JobListItem + toàn bộ chi tiết (mô tả, yêu cầu, kỹ năng, ngành học...)
"""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ApplicationStatus, JobStatus, WorkMode
from app.schemas.common import ORMModel

MAX_MONEY = 2_000_000_000  # cột salary_* là INT UNSIGNED


# ---------------------------------------------------------------- Rút gọn các bảng liên quan
class CompanyBrief(ORMModel):
    id: int
    name: str
    logo_url: Optional[str] = None


class JobTypeBrief(ORMModel):
    id: int
    code: str
    name: str


class IndustryBrief(ORMModel):
    id: int
    name: str


class SkillBrief(ORMModel):
    id: int
    name: str


class MajorBrief(ORMModel):
    id: int
    code: str
    name: str


# ---------------------------------------------------------------- Dữ liệu vào
class JobSkillIn(BaseModel):
    skill_id: int = Field(ge=1)
    is_required: bool = Field(default=True, description="True = bắt buộc, False = ưu tiên")


def _check_unique_skills(value: Optional[list[JobSkillIn]]) -> Optional[list[JobSkillIn]]:
    if value is not None:
        ids = [item.skill_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Kỹ năng bị trùng trong danh sách")
    return value


def _dedupe_ids(value: Optional[list[int]]) -> Optional[list[int]]:
    if value is None:
        return None
    return list(dict.fromkeys(value))


class JobCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255, examples=["Thực tập sinh Backend Python"])
    position: str = Field(min_length=1, max_length=255, examples=["Backend Developer"])
    job_type_id: int = Field(ge=1)
    industry_id: Optional[int] = Field(default=None, ge=1)
    term_id: Optional[int] = Field(
        default=None, ge=1, description="Có giá trị = tin thuộc đợt thực tập; bỏ trống = ứng tuyển tự do"
    )
    description: str = Field(min_length=1)
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    quantity: int = Field(default=1, ge=1, le=10000)
    salary_min: Optional[int] = Field(default=None, ge=0, le=MAX_MONEY)
    salary_max: Optional[int] = Field(default=None, ge=0, le=MAX_MONEY)
    is_salary_negotiable: bool = False
    location: Optional[str] = Field(default=None, max_length=255)
    work_mode: WorkMode = WorkMode.ONSITE
    min_gpa: Optional[float] = Field(default=None, ge=0, le=4)
    min_experience_months: Optional[int] = Field(default=None, ge=0, le=600)
    deadline: date
    skills: list[JobSkillIn] = Field(default_factory=list)
    major_ids: list[int] = Field(default_factory=list, description="Rỗng = mọi ngành được ứng tuyển")

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, value):
        return _check_unique_skills(value)

    @field_validator("major_ids")
    @classmethod
    def validate_major_ids(cls, value):
        return _dedupe_ids(value)


class JobUpdate(BaseModel):
    """Tất cả trường đều tùy chọn; trường không gửi = giữ nguyên.

    `skills` / `major_ids`: nếu gửi thì thay thế toàn bộ danh sách cũ.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    position: Optional[str] = Field(default=None, min_length=1, max_length=255)
    job_type_id: Optional[int] = Field(default=None, ge=1)
    industry_id: Optional[int] = Field(default=None, ge=1)
    term_id: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = Field(default=None, min_length=1)
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=1, le=10000)
    salary_min: Optional[int] = Field(default=None, ge=0, le=MAX_MONEY)
    salary_max: Optional[int] = Field(default=None, ge=0, le=MAX_MONEY)
    is_salary_negotiable: Optional[bool] = None
    location: Optional[str] = Field(default=None, max_length=255)
    work_mode: Optional[WorkMode] = None
    min_gpa: Optional[float] = Field(default=None, ge=0, le=4)
    min_experience_months: Optional[int] = Field(default=None, ge=0, le=600)
    deadline: Optional[date] = None
    skills: Optional[list[JobSkillIn]] = None
    major_ids: Optional[list[int]] = None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, value):
        return _check_unique_skills(value)

    @field_validator("major_ids")
    @classmethod
    def validate_major_ids(cls, value):
        return _dedupe_ids(value)


class JobFilter(BaseModel):
    """Bộ lọc tìm kiếm tin của sinh viên."""

    q: Optional[str] = Field(default=None, description="Từ khóa trong tiêu đề, vị trí, mô tả")
    position: Optional[str] = None
    location: Optional[str] = None
    major_id: Optional[int] = Field(
        default=None, description="Tin dành cho ngành này hoặc không giới hạn ngành"
    )
    industry_id: Optional[int] = None
    job_type_id: Optional[int] = None
    work_mode: Optional[WorkMode] = None
    flow: Optional[Literal["free", "term"]] = Field(
        default=None, description="free = ứng tuyển tự do, term = theo đợt"
    )
    skill_ids: list[int] = Field(
        default_factory=list, description="Tin yêu cầu ít nhất một trong các kỹ năng này"
    )
    salary_from: Optional[int] = Field(default=None, ge=0, description="Lương tối đa của tin >= giá trị này")
    salary_to: Optional[int] = Field(default=None, ge=0, description="Lương tối thiểu của tin <= giá trị này")


# ---------------------------------------------------------------- Dữ liệu ra
class JobSkillRead(ORMModel):
    skill_id: int
    is_required: bool
    skill: SkillBrief


class JobMajorRead(ORMModel):
    major_id: int
    major: MajorBrief


class JobListItem(ORMModel):
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
    company: CompanyBrief
    job_type: JobTypeBrief


class JobMyItem(JobListItem):
    """Dòng trong danh sách tin của doanh nghiệp."""

    view_count: int
    application_count: int = 0
    reject_reason: Optional[str] = None


class JobRead(JobListItem):
    description: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    min_gpa: Optional[float] = None
    min_experience_months: Optional[int] = None
    industry: Optional[IndustryBrief] = None
    view_count: int
    approved_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    updated_at: datetime
    skills: list[JobSkillRead] = []
    majors: list[JobMajorRead] = []

    @field_validator("min_gpa", mode="before")
    @classmethod
    def decimal_to_float(cls, value):
        # Cột Numeric trả Decimal; chuyển sang float để JSON là số, không phải chuỗi
        return float(value) if value is not None else None


class ViewsByDay(BaseModel):
    day: date
    views: int


class JobStats(BaseModel):
    job_id: int
    total_views: int
    total_applications: int
    views_by_day: list[ViewsByDay]
    applications_by_status: dict[ApplicationStatus, int]
