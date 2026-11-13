"""Product defaults, configurable by administrators; amounts are VND."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.freelancer_common import MoneyVnd


class FreelancerPolicyValues(BaseModel):
    model_config = ConfigDict(extra="forbid")
    small_project_threshold: MoneyVnd = 2000000
    client_max_project_amount: MoneyVnd = 20000000
    client_max_open_projects: int = Field(default=3, ge=1, le=1000)
    verified_max_project_amount: MoneyVnd = 20000000
    verified_max_open_projects: int = Field(default=5, ge=1, le=1000)
    verified_max_daily_funding: MoneyVnd = 50000000
    partner_max_project_amount: MoneyVnd = 100000000
    partner_max_open_projects: int = Field(default=20, ge=1, le=1000)
    partner_max_daily_funding: MoneyVnd = 200000000
    evidence_period_seconds: int = Field(default=604800, ge=3600, le=2592000)
    second_approval_threshold: MoneyVnd = 5000000
    review_period_seconds: int = Field(default=604800, ge=3600, le=2592000)
    offer_period_seconds: int = Field(default=604800, ge=3600, le=2592000)
    grace_period_seconds: int = Field(default=259200, ge=0, le=2592000)
    max_revision_count: int = Field(default=3, ge=0, le=100)
    fee_rate_bp: int = Field(default=500, ge=0, lt=10000)
    allow_before_start_cancellation: bool = False
    allow_overdue_cancellation: bool = False


class PolicyUpdate(BaseModel):
    values: FreelancerPolicyValues
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=2000)
