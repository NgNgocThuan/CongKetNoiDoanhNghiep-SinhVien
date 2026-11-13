from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.freelancer_enums import FundingPolicy
from app.schemas.freelancer_common import EntityId, EscrowMoneyVnd, MoneyVnd
from app.services.freelancer_accounts.common import as_naive_utc


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Proposal(Input):
    title: str = Field(min_length=1, max_length=255)
    amount: MoneyVnd
    acceptance_criteria: str = Field(min_length=1, max_length=20000)
    due_at: datetime

    @field_validator("due_at")
    @classmethod
    def utc(cls, v):
        return as_naive_utc(v)


class ProjectCreate(Input):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=50000)
    budget_amount: MoneyVnd | None = None
    max_students: int = Field(default=1, ge=1, le=1000)
    deadline: datetime | None = None
    recruitment_deadline: datetime | None = None
    category: (
        Literal["DEVELOPMENT", "DESIGN", "CONTENT", "MARKETING", "DATA", "TRANSLATION", "OTHER"]
        | None
    ) = None
    experience_level: Literal["ENTRY", "INTERMEDIATE", "ADVANCED"] | None = None
    acceptance_criteria: str = Field(default="", max_length=20000)
    deliverables_description: str = Field(default="", max_length=20000)
    funding_policy: FundingPolicy = FundingPolicy.FULL
    proposals: list[Proposal] = Field(default_factory=list, max_length=100)
    skill_ids: list[EntityId] = Field(default_factory=list, max_length=100)
    attachment_file_ids: list[EntityId] = Field(default_factory=list, max_length=10)

    @field_validator("deadline", "recruitment_deadline")
    @classmethod
    def utc(cls, v):
        return as_naive_utc(v) if v is not None else None


class ApplicationCreate(Input):
    proposal: str = Field(min_length=1, max_length=20000)
    quoted_amount: MoneyVnd
    estimated_days: int = Field(ge=1, le=3650)
    cv_id: EntityId | None = None
    cv_snapshot_file_id: EntityId | None = None


class SelectStudent(Input):
    application_id: EntityId
    allocated_amount: EscrowMoneyVnd


class ReviewInput(Input):
    reason: str = Field(default="", max_length=2000)


class BudgetUpdate(Input):
    allocated_amount: MoneyVnd


class Expansion(Input):
    budget_amount: MoneyVnd
    max_students: int = Field(ge=1, le=1000)
    reason: str = Field(min_length=1, max_length=2000)


class Resource(BaseModel):
    data: dict


class ResourcePage(BaseModel):
    items: list[dict]
    total: int
    page: int
    size: int
    pages: int
