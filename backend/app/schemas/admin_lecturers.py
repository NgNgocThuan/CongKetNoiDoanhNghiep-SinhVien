"""Schema Pydantic: Nhà trường: quản lý giảng viên. Người phụ trách: TV2.

Khuôn mẫu: app/schemas/catalog.py  (XBase -> XCreate -> XUpdate(Optional) -> XRead(ORMModel)).
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ORMModel


class LecturerBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: Optional[str] = Field(default=None, min_length=1, max_length=30, examples=["GV001"])
    full_name: str = Field(min_length=1, max_length=255, examples=["Nguyễn Văn A"])
    faculty_id: int
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)


class LecturerCreate(LecturerBase):
    pass


class LecturerUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    faculty_id: Optional[int] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


class LecturerRead(ORMModel, LecturerBase):
    id: int
    is_active: bool
