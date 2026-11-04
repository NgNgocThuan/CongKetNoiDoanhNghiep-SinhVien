"""Interfaces only. In-TX implementations must never commit or call a network."""
from datetime import datetime
from typing import Literal, Protocol

from sqlalchemy.orm import Session

from app.contracts.freelancer.types import (
    AcceptanceRef,
    ClientEligibility,
    CommandContext,
    ContractRef,
    DisputeRef,
    FundingState,
    MilestoneFinancialTerms,
    ProjectClosureState,
    SettlementRef,
)


class EligibilityPort(Protocol):
    def get_client_eligibility(self, db: Session, *, user_id: int, now_utc: datetime) -> ClientEligibility: ...
    def assert_student_eligible(self, db: Session, *, student_id: int, now_utc: datetime) -> None: ...
    def assert_contract_party(self, db: Session, *, contract_id: int, actor_user_id: int) -> None: ...
    def assert_project_owner(self, db: Session, *, project_id: int, actor_user_id: int) -> None: ...


class ContractPort(Protocol):
    def create_contract_for_selected_application_in_tx(
        self, db: Session, *, ctx: CommandContext, project_id: int,
        application_id: int, allocated_amount: int,
    ) -> ContractRef: ...

    def get_milestone_financial_terms(self, db: Session, *, milestone_id: int) -> MilestoneFinancialTerms: ...


class WorkPort(Protocol):
    def record_acceptance_in_tx(
        self, db: Session, *, ctx: CommandContext, milestone_id: int,
        deliverable_id: int, source: Literal["MANUAL", "AUTO"],
    ) -> AcceptanceRef: ...


class FinancePort(Protocol):
    def get_funding_state(self, db: Session, *, milestone_id: int) -> FundingState: ...
    def assert_can_start_in_tx(self, db: Session, *, ctx: CommandContext, milestone_id: int) -> None: ...
    def assert_disputable_in_tx(self, db: Session, *, ctx: CommandContext, milestone_id: int) -> None: ...

    def prepare_acceptance_settlement_in_tx(self, db: Session, *, ctx: CommandContext, review_id: int) -> SettlementRef: ...
    def prepare_decision_settlement_in_tx(self, db: Session, *, ctx: CommandContext, decision_id: int) -> SettlementRef: ...
    def prepare_cancellation_settlement_in_tx(self, db: Session, *, ctx: CommandContext, cancellation_id: int) -> SettlementRef: ...


class HoldPort(Protocol):
    def place_hold_in_tx(
        self, db: Session, *, ctx: CommandContext, milestone_id: int,
        reason_type: str, reason_key: str, dispute_id: int | None, note: str,
    ) -> int: ...

    def release_hold_in_tx(self, db: Session, *, ctx: CommandContext, hold_id: int, note: str) -> None: ...


class DisputePort(Protocol):
    def open_dispute(
        self, db: Session, *, ctx: CommandContext, milestone_id: int,
        reason_code: str, description: str,
    ) -> DisputeRef: ...


class ClosurePort(Protocol):
    def recompute_contract_closure_in_tx(self, db: Session, *, ctx: CommandContext, contract_id: int) -> None: ...
    def get_project_closure_state(self, db: Session, *, project_id: int) -> ProjectClosureState: ...
    def recompute_project_closure_in_tx(self, db: Session, *, ctx: CommandContext, project_id: int) -> None: ...
