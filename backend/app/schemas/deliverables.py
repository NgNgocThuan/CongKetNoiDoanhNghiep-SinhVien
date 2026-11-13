"""Pydantic schemas for deliverables and milestone reviews."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.freelancer_enums import MilestoneReviewAction
from app.schemas.freelancer_common import EntityId


class DeliverableCreate(BaseModel):
    file_ids: list[EntityId] = []
    note: str | None = None


class DeliverableFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: EntityId
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class MilestoneReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    milestone_id: EntityId
    deliverable_id: EntityId
    reviewed_by: EntityId | None = None
    action: MilestoneReviewAction
    reason: str | None = None
    reviewed_at: datetime


class DeliverableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    milestone_id: EntityId
    submission_no: int
    submitted_by: EntityId
    note: str | None = None
    submitted_at: datetime
    files: list[DeliverableFileRead] = []
    reviews: list[MilestoneReviewRead] = []
