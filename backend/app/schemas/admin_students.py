"""Schema Pydantic: Nhà trường: quản lý dữ liệu sinh viên. Người phụ trách: TV2.

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    AchievementType,
    CertificateSource,
    ImportType,
    SkillLevel,
    SkillSource,
    UserStatus,
)
from app.schemas.common import ORMModel


class AdminStudentRead(BaseModel):
    """Dòng trong danh sách sinh viên (dữ liệu chính thức từ nhà trường + trạng thái tài khoản)."""

    id: int
    user_id: int
    student_code: str
    full_name: str
    email: str
    account_status: UserStatus
    date_of_birth: Optional[date] = None
    class_name: Optional[str] = None
    faculty_id: int
    faculty_name: str
    major_id: int
    major_name: str
    cohort: str
    gpa: Optional[Decimal] = None
    academic_result: Optional[str] = None
    phone: Optional[str] = None
    synced_at: Optional[datetime] = None


class StudentAcademicUpdate(BaseModel):
    """Cập nhật dữ liệu học thuật (chỉ nhà trường được sửa). Trường nào không gửi thì giữ nguyên."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    class_name: Optional[str] = Field(default=None, max_length=50)
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    cohort: Optional[str] = Field(default=None, min_length=1, max_length=20)
    gpa: Optional[Decimal] = Field(default=None, ge=0, le=4, max_digits=3, decimal_places=2)
    academic_result: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)


# ---------------------------------------------------------------- Thành tích / chứng chỉ
class AchievementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: AchievementType = AchievementType.ACHIEVEMENT
    title: str = Field(min_length=1, max_length=255, examples=["Giải nhì Olympic Tin học"])
    description: Optional[str] = None
    achieved_at: Optional[date] = None


class AchievementRead(ORMModel):
    id: int
    student_id: int
    type: AchievementType
    title: str
    description: Optional[str] = None
    achieved_at: Optional[date] = None


class CertificateRead(ORMModel):
    id: int
    student_id: int
    name: str
    issuer: Optional[str] = None
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    credential_url: Optional[str] = None
    source: CertificateSource
    is_verified: bool
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None


# ---------------------------------------------------------------- Chi tiết sinh viên (tách rõ nguồn dữ liệu)
class SelfSkillRead(BaseModel):
    skill_id: int
    name: str
    level: SkillLevel
    source: SkillSource


class SelfProfileRead(ORMModel):
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    career_goal: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    is_open_to_work: bool
    show_gpa: bool
    show_contact: bool
    show_achievements: bool


class SelfExperienceRead(ORMModel):
    id: int
    company_name: str
    position: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class SelfProjectRead(ORMModel):
    id: int
    name: str
    role: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    project_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class OfficialStudentData(BaseModel):
    """Dữ liệu do nhà trường quản lý (sinh viên không tự sửa)."""

    academic: AdminStudentRead
    achievements: list[AchievementRead]
    school_certificates: list[CertificateRead]


class SelfDeclaredStudentData(BaseModel):
    """Dữ liệu sinh viên tự khai; chưa được nhà trường xác nhận trừ chứng chỉ có is_verified."""

    profile: Optional[SelfProfileRead] = None
    skills: list[SelfSkillRead]
    experiences: list[SelfExperienceRead]
    projects: list[SelfProjectRead]
    certificates: list[CertificateRead]


class AdminStudentDetail(BaseModel):
    official: OfficialStudentData
    self_declared: SelfDeclaredStudentData


# ---------------------------------------------------------------- Import
class ImportRowError(BaseModel):
    row: int = Field(description="Số dòng trong file (dòng 1 là header, dữ liệu bắt đầu từ dòng 2)")
    key: Optional[str] = Field(default=None, description="Mã sinh viên của dòng lỗi (nếu đọc được)")
    message: str


class ImportBatchRead(ORMModel):
    id: int
    type: ImportType
    file_name: Optional[str] = None
    total_rows: int
    success_rows: int
    failed_rows: int
    imported_by: int
    created_at: datetime


class ImportBatchDetail(ImportBatchRead):
    errors: list[ImportRowError] = []


class ImportResult(BaseModel):
    """Kết quả một lần import: thông tin lô + danh sách dòng lỗi."""

    batch: ImportBatchDetail
    activation_emails_queued: int = Field(description="Số email kích hoạt đã xếp hàng gửi")
