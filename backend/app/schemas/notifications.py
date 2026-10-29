"""Schema Pydantic: Thông báo trong ứng dụng. Người phụ trách: TV1."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: int
    user_id: int
    type: str
    title: str
    content: Optional[str] = None
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    is_read: bool
    created_at: datetime


class UnreadCountRead(BaseModel):
    unread_count: int


class MarkAllReadResponse(BaseModel):
    updated_count: int
    message: str
