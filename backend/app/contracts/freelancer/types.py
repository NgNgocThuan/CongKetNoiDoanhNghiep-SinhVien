"""Python DTOs use integer IDs/VND; HTTP serialization is a separate concern."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.core.freelancer_enums import (
    ActorType,
    ContractStatus,
    DisputeStatus,
    FundingPolicy,
    ProjectStatus,
    RecruitmentStatus,
    SettlementKind,
    SettlementStatus,
)


@dataclass(frozen=True, kw_only=True)
class CommandContext:
    actor_user_id: int | None
    actor_type: ActorType
    request_id: str
    idempotency_key: str | None
    now_utc: datetime
    job_key: str | None = None

    def __post_init__(self) -> None:
        if self.actor_type == ActorType.USER and not self.actor_user_id:
            raise ValueError("USER commands require an authenticated actor")
        if not self.request_id:
            raise ValueError("request_id is required")
        if self.actor_type not in tuple(ActorType):
            raise ValueError("Invalid actor type")
        if self.now_utc.utcoffset() is not None and self.now_utc.utcoffset().total_seconds() != 0:
            raise ValueError("Command timestamps must be UTC")


@dataclass(frozen=True, kw_only=True)
class ClientEligibility:
    user_id: int
    company_id: int | None
    tier: str
    can_draft: bool
    can_submit: bool
    can_fund: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class ContractRef:
    contract_id: int
    project_id: int
    student_id: int
    status: ContractStatus
    allocated_amount: int


@dataclass(frozen=True, kw_only=True)
class MilestoneFinancialTerms:
    milestone_id: int
    contract_id: int
    client_user_id: int
    student_user_id: int
    amount: int
    fee_rate_bp: int
    funding_policy: FundingPolicy
    terms_id: int


@dataclass(frozen=True, kw_only=True)
class FundingState:
    milestone_id: int
    funded_amount: int
    held_amount: int
    reserved_amount: int
    active_hold_ids: tuple[int, ...]
    is_fully_funded: bool


@dataclass(frozen=True, kw_only=True)
class AcceptanceRef:
    review_id: int
    milestone_id: int
    deliverable_id: int
    source: Literal["MANUAL", "AUTO"]
    accepted_at: datetime


@dataclass(frozen=True, kw_only=True)
class SettlementRef:
    settlement_id: int
    milestone_id: int
    kind: SettlementKind
    status: SettlementStatus


@dataclass(frozen=True, kw_only=True)
class DisputeRef:
    dispute_id: int
    milestone_id: int
    status: DisputeStatus
    evidence_deadline: datetime


@dataclass(frozen=True, kw_only=True)
class ProjectClosureState:
    project_id: int
    recruitment_status: RecruitmentStatus
    contract_counts: tuple[tuple[str, int], ...]
    has_open_obligations: bool
    eligible_terminal_status: ProjectStatus | None
