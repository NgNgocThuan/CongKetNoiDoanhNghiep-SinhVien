"""Pydantic schemas for CV management."""

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import CVType
from app.schemas.common import ORMModel
from app.schemas.school_common import SchoolUpdate


class CVOnlineCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    content_json: dict[str, Any] = Field(
        default_factory=dict,
        description="Nội dung tự khai; phần official được backend tự điền từ nhà trường",
    )


class CVUpdate(SchoolUpdate):
    required_non_null: ClassVar[tuple[str, ...]] = ("title",)
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content_json: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def require_change(self):
        if "title" not in self.model_fields_set and "content_json" not in self.model_fields_set:
            raise ValueError("Cần gửi ít nhất một trường để cập nhật")
        return self


class CVRead(ORMModel):
    id: int
    student_id: int
    title: str
    type: CVType
    file_url: Optional[str] = None
    content_json: Optional[dict[str, Any]] = None
    is_default: bool
    parsed_json: Optional[dict[str, Any]] = None
    parsed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CVAnalysisRead(BaseModel):
    cv_id: int
    parsed_json: dict[str, Any]
