"""Pydantic schemas for freelance reviews."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.freelancer_enums import ReviewVisibility
from app.schemas.freelancer_common import EntityId


class FreelanceReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class FreelanceReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    contract_id: EntityId
    reviewer_user_id: EntityId
    reviewee_user_id: EntityId
    rating: int
    comment: str | None = None
    visibility: ReviewVisibility
    created_at: datetime
