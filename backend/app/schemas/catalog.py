"""Schema danh mục. Người phụ trách: TV2.

Đã làm mẫu cho Faculty. TODO(TV2): Major, Industry, JobType, Skill, SkillAlias theo cùng khuôn:
  XBase (trường chung) -> XCreate -> XUpdate (tất cả Optional) -> XRead (ORMModel, có id).
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel


class FacultyBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=30, examples=["CNTT"])
    name: str = Field(min_length=1, max_length=255, examples=["Công nghệ thông tin"])


class FacultyCreate(FacultyBase):
    pass


class FacultyUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class FacultyRead(ORMModel, FacultyBase):
    id: int
    is_active: bool
