"""Schema Pydantic: Đơn ứng tuyển và chi tiết đơn."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import ApplicationStatus
from app.schemas.common import ORMModel


class StatusLogRead(ORMModel):
    id: int
    application_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[int] = None
    note: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = Field(default=None, max_length=500)


class StudentInfoNested(ORMModel):
    """Thông tin sinh viên lồng nhau phục vụ bộ lọc kinh nghiệm và test."""
    id: int
    full_name: Optional[str] = None
    gpa: Optional[float] = None
    experience_months: int = 0
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ApplicationRead(ORMModel):
    """Schema chuẩn cho danh sách ứng viên, chi tiết và cập nhật trạng thái."""
    id: int
    job_id: int
    student_id: int
    cv_id: int
    current_status: ApplicationStatus
    cover_letter: Optional[str] = None
    applied_at: datetime = Field(..., validation_alias="applied_at")
    updated_at: datetime
    
    # Trường liên hệ ở tầng root
    contact_email: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)
    
    # Đối tượng sinh viên lồng nhau chứa experience_months
    student: Optional[StudentInfoNested] = Field(default=None)
    
    status_logs: List[StatusLogRead] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def extract_application_data(cls, values):
        if values is None:
            return values
        
        if not isinstance(values, dict):
            app = values
            data = {
                "id": getattr(app, "id", None),
                "job_id": getattr(app, "job_id", None),
                "student_id": getattr(app, "student_id", None),
                "cv_id": getattr(app, "cv_id", None),
                "current_status": getattr(app, "current_status", None),
                "cover_letter": getattr(app, "cover_letter", None),
                "applied_at": getattr(app, "applied_at", None),
                "updated_at": getattr(app, "updated_at", None),
                "status_logs": getattr(app, "status_logs", []),
            }
            
            student = getattr(app, "student", None)
            if student:
                show = True
                profile = getattr(student, "profile", None)
                if profile is not None:
                    show = getattr(profile, "show_contact", True)
                
                email = None
                phone = None
                if show:
                    if profile is not None:
                        email = getattr(profile, "contact_email", None)
                        phone = getattr(profile, "contact_phone", None)
                    if not email:
                        user = getattr(student, "user", None)
                        email = getattr(user, "email", None)
                    if not phone:
                        phone = getattr(student, "phone", None)
                
                data["contact_email"] = email
                data["contact_phone"] = phone
                
                # Tính tổng số tháng kinh nghiệm từ student_experiences
                total_exp = getattr(student, "experience_months", None)
                if total_exp is None:
                    today = date.today()
                    total_exp = 0
                    experiences = getattr(student, "experiences", [])
                    if experiences:
                        for exp in experiences:
                            start = getattr(exp, "start_date", None)
                            if start:
                                end = getattr(exp, "end_date", None) or today
                                total_exp += max(0, (end.year - start.year) * 12 + (end.month - start.month))
                
                skills = getattr(student, "skills", [])
                skills_list = [s.name if hasattr(s, "name") else str(s) for s in skills]
                
                data["student"] = {
                    "id": getattr(student, "id", None),
                    "full_name": getattr(student, "full_name", None),
                    "gpa": getattr(student, "gpa", None),
                    "experience_months": total_exp,
                    "skills": skills_list,
                }
            else:
                data["contact_email"] = None
                data["contact_phone"] = None
                data["student"] = None
                
            return data
            
        return values


class ApplicationDetail(ApplicationRead):
    """Schema chi tiết đơn ứng tuyển."""
    pass