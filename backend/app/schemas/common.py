"""Schema dùng chung: base ORM, phân trang, thông điệp."""
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base cho schema đọc từ SQLAlchemy model (response)."""

    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class Message(BaseModel):
    message: str
