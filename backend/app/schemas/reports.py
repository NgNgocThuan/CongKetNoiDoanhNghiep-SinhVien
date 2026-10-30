"""Schema Pydantic: Báo cáo vi phạm. Người phụ trách: TV1."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ReportStatus, ReportTargetType
from app.schemas.common import ORMModel


class ReportCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    target_type: ReportTargetType
    target_id: int = Field(gt=0, description="ID của đối tượng bị báo cáo")
    reason: str = Field(min_length=1, max_length=500, description="Lý do báo cáo vi phạm")


class ReportHandle(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    status: ReportStatus = Field(description="RESOLVED hoặc REJECTED")
    resolution_note: Optional[str] = Field(default=None, max_length=500)
    lock_target_user: bool = Field(default=False, description="Tự động khóa tài khoản đối tượng vi phạm nếu RESOLVED")
    close_target_job: bool = Field(default=False, description="Tự động đóng tin tuyển dụng vi phạm nếu RESOLVED")


class ReportRead(ORMModel):
    id: int
    reporter_id: int
    target_type: ReportTargetType
    target_id: int
    reason: str
    status: ReportStatus
    handled_by: Optional[int] = None
    handled_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_at: datetime
