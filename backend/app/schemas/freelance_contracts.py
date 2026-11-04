"""Pydantic schemas for freelance contracts and contract versions."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.freelancer_enums import (
    ContractStatus,
    ContractVersionStatus,
    FundingPolicy,
)
from app.schemas.freelancer_common import EntityId, MoneyVnd


class MilestoneTermInput(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    amount: MoneyVnd
    acceptance_criteria: str
    due_at: datetime
    included: bool = True


class ContractVersionCreate(BaseModel):
    total_amount: MoneyVnd
    fee_rate_bp: int | None = 500
    review_period_seconds: int | None = 604800
    max_revision_count: int | None = 3
    grace_period_seconds: int | None = 259200
    funding_policy: FundingPolicy
    terms_json: dict | None = None
    terms: dict | None = Field(default=None, exclude=True)
    milestone_terms: list[MilestoneTermInput]

    @model_validator(mode="after")
    def populate_terms_json(self) -> "ContractVersionCreate":
        if self.terms_json is None and self.terms is not None:
            self.terms_json = self.terms
        return self


class ContractVersionOfferRequest(BaseModel):
    acceptance_deadline: datetime | None = None


class ContractVersionAcceptRequest(BaseModel):
    content_hash: str


class ContractVersionDeclineRequest(BaseModel):
    response_note: str | None = None


class ContractMilestoneTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    milestone_id: EntityId
    title: str
    description: str | None = None
    amount: MoneyVnd
    acceptance_criteria: str
    due_at: datetime
    included: bool


class ContractVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    contract_id: EntityId
    version_no: int
    created_by: EntityId
    status: ContractVersionStatus
    total_amount: MoneyVnd
    fee_rate_bp: int
    review_period_seconds: int
    max_revision_count: int
    grace_period_seconds: int
    funding_policy: FundingPolicy
    terms_json: dict
    content_hash: str | None = None
    offered_at: datetime | None = None
    acceptance_deadline: datetime | None = None
    client_accepted_at: datetime | None = None
    freelancer_accepted_at: datetime | None = None
    effective_at: datetime | None = None
    response_note: str | None = None
    milestone_terms: list[ContractMilestoneTermRead] = []
    created_at: datetime


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EntityId
    project_id: EntityId
    application_id: EntityId
    client_user_id: EntityId
    company_id: EntityId | None = None
    freelancer_student_id: EntityId
    status: ContractStatus
    effective_version_id: EntityId | None = None
    activated_at: datetime | None = None
    closed_at: datetime | None = None
    closure_reason: str | None = None
    created_at: datetime
    allocated_amount: MoneyVnd | None = None
    effective_version: ContractVersionRead | None = None
