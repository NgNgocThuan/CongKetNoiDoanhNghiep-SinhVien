"""Pydantic schemas for the student-owned profile API."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.enums import AchievementType, CertificateSource, SkillLevel, SkillSource
from app.schemas.common import ORMModel


class FacultyBrief(ORMModel):
    id: int
    code: str
    name: str


class MajorBrief(ORMModel):
    id: int
    code: str
    name: str


class StudentOfficialRead(ORMModel):
    id: int
    student_code: str
    full_name: str
    date_of_birth: Optional[date] = None
    class_name: Optional[str] = None
    cohort: str
    gpa: Optional[Decimal] = None
    academic_result: Optional[str] = None
    phone: Optional[str] = None
    faculty: FacultyBrief
    major: MajorBrief
    synced_at: Optional[datetime] = None
    certificates: list["CertificateRead"] = Field(default_factory=list)
    achievements: list["AchievementRead"] = Field(default_factory=list)


class ProfileRead(ORMModel):
    student_id: int
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    career_goal: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    is_open_to_work: bool
    show_gpa: bool
    show_contact: bool
    show_achievements: bool
    updated_at: datetime


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = None
    career_goal: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    linkedin_url: Optional[str] = Field(default=None, max_length=500)
    github_url: Optional[str] = Field(default=None, max_length=500)
    is_open_to_work: Optional[bool] = None
    show_gpa: Optional[bool] = None
    show_contact: Optional[bool] = None
    show_achievements: Optional[bool] = None


class SkillCreate(BaseModel):
    skill_id: int = Field(ge=1)
    level: SkillLevel = SkillLevel.BEGINNER


class SkillUpdate(BaseModel):
    level: SkillLevel


class SkillItem(ORMModel):
    skill_id: int
    level: SkillLevel
    source: SkillSource
    created_at: datetime
    name: str


class ExperienceBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc không được trước ngày bắt đầu")
        return self


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    position: Optional[str] = Field(default=None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class ExperienceRead(ORMModel, ExperienceBase):
    id: int
    student_id: int


class ProjectBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    role: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    tech_stack: Optional[str] = Field(default=None, max_length=500)
    project_url: Optional[str] = Field(default=None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc không được trước ngày bắt đầu")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    tech_stack: Optional[str] = Field(default=None, max_length=500)
    project_url: Optional[str] = Field(default=None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectRead(ORMModel, ProjectBase):
    id: int
    student_id: int


class CertificateBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    issuer: Optional[str] = Field(default=None, max_length=255)
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    credential_url: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.issued_at and self.expires_at and self.expires_at < self.issued_at:
            raise ValueError("Ngày hết hạn không được trước ngày cấp")
        return self


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    issuer: Optional[str] = Field(default=None, max_length=255)
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    credential_url: Optional[str] = Field(default=None, max_length=500)


class CertificateRead(ORMModel, CertificateBase):
    id: int
    student_id: int
    source: CertificateSource
    is_verified: bool
    verified_at: Optional[datetime] = None


class AchievementRead(ORMModel):
    id: int
    type: AchievementType
    title: str
    description: Optional[str] = None
    achieved_at: Optional[date] = None


class StudentSelfRead(BaseModel):
    profile: ProfileRead
    skills: list[SkillItem] = Field(default_factory=list)
    experiences: list[ExperienceRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)
    certificates: list[CertificateRead] = Field(default_factory=list)


class StudentFullProfile(BaseModel):
    official: StudentOfficialRead
    self_declared: StudentSelfRead


class LecturerBrief(ORMModel):
    id: int
    code: Optional[str] = None
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class InternshipTermBrief(ORMModel):
    id: int
    name: str
    semester: str
    academic_year: str
    start_date: date
    end_date: date
    status: Any


class InternshipAssignmentRead(ORMModel):
    id: int
    term: InternshipTermBrief
    lecturer: Optional[LecturerBrief] = None


StudentOfficialRead.model_rebuild()
