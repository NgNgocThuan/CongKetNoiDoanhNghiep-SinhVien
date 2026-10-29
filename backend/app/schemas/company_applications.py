"""Schema Pydantic: Quản lý ứng viên (Kanban). Người phụ trách: Khôi."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.core.enums import ApplicationStatus
from app.schemas.common import ORMModel
from app.schemas.applications import StatusLogRead


class CompanyApplicationBase(BaseModel):
    cover_letter: Optional[str] = Field(default=None, max_length=1000)


class CompanyApplicationCreate(CompanyApplicationBase):
    job_id: int = Field(ge=1)
    cv_id: int = Field(ge=1)


class CompanyApplicationUpdate(BaseModel):
    cover_letter: Optional[str] = Field(default=None, max_length=1000)


class StudentInfoNested(ORMModel):
    """Đối tượng sinh viên lồng nhau phục vụ bộ lọc kinh nghiệm và test."""
    id: int
    full_name: Optional[str] = None
    gpa: Optional[float] = None
    experience_months: int = 0
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class CompanyApplicationRead(ORMModel):
    """Schema trả về thông tin chi tiết đơn ứng tuyển cho doanh nghiệp."""
    id: int
    job_id: int
    student_id: int
    cv_id: int
    current_status: ApplicationStatus
    cover_letter: Optional[str] = None
    applied_at: datetime = Field(..., validation_alias="applied_at")
    updated_at: datetime
    
    # Đưa contact ra tầng root để khớp với test_detail_hides_contact / shows_contact
    contact_email: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)
    
    # Đối tượng sinh viên lồng nhau phục vụ test_list_applications_and_experience_filter
    student: Optional[StudentInfoNested] = Field(default=None)
    
    status_logs: List[StatusLogRead] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if hasattr(obj, "student") and obj.student:
            st = obj.student
            
            # 1. Kiểm tra quyền ẩn/hiện email (show_contact)
            show = True
            if hasattr(st, "profile") and st.profile is not None:
                show = getattr(st.profile, "show_contact", True)
            
            email = getattr(st.user, "email", None) if (show and st.user) else None
            phone = getattr(st, "phone", None)
            
            if hasattr(obj, "__dict__"):
                object.__setattr__(obj, "contact_email", email)
                object.__setattr__(obj, "contact_phone", phone)
                
                # 2. Tính tổng số tháng kinh nghiệm từ bảng student_experiences
                total_exp = getattr(st, "experience_months", None)
                if total_exp is None:
                    from datetime import date
                    today = date.today()
                    total_exp = 0
                    if hasattr(st, "experiences") and st.experiences:
                        for exp in st.experiences:
                            if getattr(exp, "start_date", None):
                                end = getattr(exp, "end_date", None) or today
                                total_exp += max(0, (end.year - exp.start_date.year) * 12 + (end.month - exp.start_date.month))
                
                skills_list = []
                if hasattr(st, "skills") and st.skills:
                    skills_list = [s.name if hasattr(s, "name") else str(s) for s in st.skills]
                
                student_data = {
                    "id": st.id,
                    "full_name": getattr(st, "full_name", None),
                    "gpa": getattr(st, "gpa", None),
                    "experience_months": total_exp,
                    "skills": skills_list
                }
                object.__setattr__(obj, "student", student_data)

        return super().model_validate(obj, *args, **kwargs)


class StatusChange(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: ApplicationStatus = Field(description="Trạng thái mới của đơn ứng tuyển")
    note: Optional[str] = Field(default=None, max_length=500, description="Ghi chú khi chuyển trạng thái")


class KanbanColumn(BaseModel):
    status: ApplicationStatus
    title: str
    items: List[CompanyApplicationRead] = Field(default_factory=list)
    total: int = 0


class KanbanBoard(BaseModel):
    job_id: int
    columns: List[KanbanColumn] = Field(default_factory=list)
    total_applications: int = 0

    model_config = ConfigDict(from_attributes=True)