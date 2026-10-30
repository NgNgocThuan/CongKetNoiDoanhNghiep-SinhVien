"""Schema Pydantic: Thực tập theo đợt & kết quả thực tập. Người phụ trách: TV2.

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
Schema response kế thừa ORMModel (app.schemas.common).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import InternshipResultStatus, JobStatus, TermStatus
from app.schemas.admin_students import ImportBatchDetail
from app.schemas.common import ORMModel


# ---------------------------------------------------------------- Đợt thực tập
class TermBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255, examples=["Thực tập doanh nghiệp HK1 2025-2026"])
    semester: str = Field(min_length=1, max_length=20, examples=["HK1"])
    academic_year: str = Field(min_length=1, max_length=20, examples=["2025-2026"])
    start_date: date
    end_date: date


class TermCreate(TermBase):
    @model_validator(mode="after")
    def _check_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc")
        return self


class TermUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    semester: Optional[str] = Field(default=None, min_length=1, max_length=20)
    academic_year: Optional[str] = Field(default=None, min_length=1, max_length=20)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TermRead(ORMModel, TermBase):
    id: int
    status: TermStatus
    created_by: int
    created_at: datetime
    student_count: int = 0


class TermStatusChange(BaseModel):
    status: TermStatus = Field(description="Chỉ được chuyển tiến một bước: DRAFT→OPEN→ONGOING→CLOSED")


# ---------------------------------------------------------------- Sinh viên trong đợt
class TermStudentAdd(BaseModel):
    student_ids: list[int] = Field(min_length=1, max_length=1000)


class TermStudentAddResult(BaseModel):
    added: int
    already_in_term: int
    not_found_ids: list[int]


class TermStudentRead(BaseModel):
    term_student_id: int
    student_id: int
    student_code: str
    full_name: str
    class_name: Optional[str] = None
    lecturer_id: Optional[int] = None
    lecturer_name: Optional[str] = None


class TermImportResult(BaseModel):
    batch: ImportBatchDetail
    added: int = Field(description="Số sinh viên đã được thêm vào đợt")


class AssignLecturers(BaseModel):
    lecturer_id: Optional[int] = Field(default=None, description="Để trống (null) để bỏ phân công")
    student_ids: list[int] = Field(min_length=1, max_length=1000)


class AssignLecturersResult(BaseModel):
    updated: int
    not_in_term_ids: list[int]


class TermJobRead(BaseModel):
    id: int
    title: str
    position: str
    company_id: int
    company_name: str
    quantity: int
    deadline: date
    status: JobStatus


# ---------------------------------------------------------------- Kết quả thực tập
class InternshipResultRead(BaseModel):
    id: int
    term_id: int
    term_student_id: int
    student_id: int
    student_code: str
    student_name: str
    lecturer_id: Optional[int] = None
    lecturer_name: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    application_id: Optional[int] = None
    company_evaluation: Optional[str] = None
    company_score: Optional[Decimal] = None
    evaluated_at: Optional[datetime] = None
    lecturer_comment: Optional[str] = None
    lecturer_score: Optional[Decimal] = None
    result: InternshipResultStatus
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None


class CompanyEvaluation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    evaluation: str = Field(min_length=1, max_length=5000, description="Nhận xét của doanh nghiệp")
    score: Decimal = Field(ge=0, le=10, max_digits=4, decimal_places=2, description="Điểm trên thang 10")


class LecturerReview(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    comment: Optional[str] = Field(default=None, max_length=5000)
    score: Optional[Decimal] = Field(default=None, ge=0, le=10, max_digits=4, decimal_places=2)

    @model_validator(mode="after")
    def _need_something(self):
        if self.comment is None and self.score is None:
            raise ValueError("Cần nhập nhận xét hoặc điểm")
        return self


class ResultConfirm(BaseModel):
    result: Literal["PASSED", "FAILED"]
