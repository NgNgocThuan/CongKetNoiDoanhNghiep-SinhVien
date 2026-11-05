"""Pydantic schemas for milestones."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.freelancer_enums import AcceptanceSource, MilestoneStatus
from app.schemas.freelance_contracts import ContractMilestoneTermRead
from app.schemas.freelancer_common import EntityId


class MilestoneAcceptRequest(BaseModel):
    deliverable_id: EntityId


class MilestoneRevisionRequest(BaseModel):
    deliverable_id: EntityId
    reason: str = Field(..., min_length=1)


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    contract_id: EntityId
    sequence_no: int
    effective_terms_id: EntityId | None = None
    status: MilestoneStatus
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    review_deadline: datetime | None = None
    revision_count: int
    accepted_at: datetime | None = None
    acceptance_source: AcceptanceSource | None = None
    settled_at: datetime | None = None
    settlement_id: EntityId | None = None
    created_at: datetime
    effective_terms: ContractMilestoneTermRead | None = None
