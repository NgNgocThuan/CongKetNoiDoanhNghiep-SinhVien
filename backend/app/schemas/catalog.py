"""Schema danh mục. Người phụ trách: TV2.

Khuôn: XBase (trường chung) -> XCreate -> XUpdate (tất cả Optional) -> XRead (ORMModel, có id).
Faculty, Major, Industry, JobType, Skill, SkillAlias.
"""

from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel
from app.schemas.school_common import SchoolUpdate


class FacultyBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=30, examples=["CNTT"])
    name: str = Field(min_length=1, max_length=255, examples=["Công nghệ thông tin"])


class FacultyCreate(FacultyBase):
    pass


class FacultyUpdate(SchoolUpdate):
    required_non_null: ClassVar[tuple[str, ...]] = ("code", "name", "is_active")
    model_config = ConfigDict(str_strip_whitespace=True)

    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class FacultyRead(ORMModel, FacultyBase):
    id: int
    is_active: bool


# ---------------------------------------------------------------- Majors
class MajorBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    faculty_id: int
    code: str = Field(min_length=1, max_length=30, examples=["KTPM"])
    name: str = Field(min_length=1, max_length=255, examples=["Kỹ thuật phần mềm"])


class MajorCreate(MajorBase):
    pass


class MajorUpdate(SchoolUpdate):
    required_non_null: ClassVar[tuple[str, ...]] = ("code", "name", "faculty_id", "is_active")
    model_config = ConfigDict(str_strip_whitespace=True)

    faculty_id: Optional[int] = None
    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class MajorRead(ORMModel, MajorBase):
    id: int
    is_active: bool


# ---------------------------------------------------------------- Industries
class IndustryBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255, examples=["Phần mềm"])


class IndustryCreate(IndustryBase):
    pass


class IndustryUpdate(SchoolUpdate):
    required_non_null: ClassVar[tuple[str, ...]] = ("name", "is_active")
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class IndustryRead(ORMModel, IndustryBase):
    id: int
    is_active: bool


# ---------------------------------------------------------------- Job types
class JobTypeBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=30, examples=["INTERN"])
    name: str = Field(min_length=1, max_length=100, examples=["Thực tập sinh"])


class JobTypeCreate(JobTypeBase):
    pass


class JobTypeUpdate(SchoolUpdate):
    required_non_null: ClassVar[tuple[str, ...]] = ("code", "name", "is_active")
    model_config = ConfigDict(str_strip_whitespace=True)

    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class JobTypeRead(ORMModel, JobTypeBase):
    id: int
    is_active: bool


# ---------------------------------------------------------------- Skills
class SkillBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100, examples=["React"])
    category: Optional[str] = Field(default=None, max_length=100, examples=["Frontend"])


class SkillCreate(SkillBase):
    pass


class SkillUpdate(SchoolUpdate):
    required_non_null: ClassVar[tuple[str, ...]] = ("name", "is_active")
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class SkillRead(ORMModel, SkillBase):
    id: int
    is_active: bool


class SkillAliasCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    alias: str = Field(min_length=1, max_length=100, examples=["ReactJS"])


class SkillAliasRead(ORMModel):
    id: int
    skill_id: int
    alias: str
