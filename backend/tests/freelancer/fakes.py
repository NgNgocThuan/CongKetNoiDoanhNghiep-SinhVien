"""Explicit test double. Never import this module from application code."""
from app.contracts.freelancer.types import FundingState, SettlementRef
from app.core.exceptions import ConflictError
from app.core.freelancer_enums import SettlementKind, SettlementStatus


class FakeFinancePort:
    def __init__(self, *, funded=False, held=False, reserved=False):
        self.funded = funded
        self.held = held
        self.reserved = reserved
        self.calls = []

    def get_funding_state(self, db, *, milestone_id):
        return FundingState(
            milestone_id=milestone_id, funded_amount=100000 if self.funded else 0,
            held_amount=100000 if self.funded else 0,
            reserved_amount=100000 if self.reserved else 0,
            active_hold_ids=(1,) if self.held else (), is_fully_funded=self.funded,
        )

    def _check(self):
        if not self.funded:
            raise ConflictError("Not funded", code="MILESTONE_NOT_FUNDED")
        if self.held:
            raise ConflictError("Held", code="FUNDS_ON_HOLD")
        if self.reserved:
            raise ConflictError("Reserved", code="FUNDS_RESERVED")

    def assert_can_start_in_tx(self, db, *, ctx, milestone_id):
        self._check()

    def assert_disputable_in_tx(self, db, *, ctx, milestone_id):
        self._check()

    def _prepare(self, kind, source_id):
        self._check()
        self.calls.append((kind, source_id))
        self.reserved = True
        return SettlementRef(
            settlement_id=1, milestone_id=1, kind=SettlementKind.RELEASE,
            status=SettlementStatus.PREPARED,
        )

    def prepare_acceptance_settlement_in_tx(self, db, *, ctx, review_id):
        return self._prepare("acceptance", review_id)

    def prepare_decision_settlement_in_tx(self, db, *, ctx, decision_id):
        return self._prepare("decision", decision_id)

    def prepare_cancellation_settlement_in_tx(self, db, *, ctx, cancellation_id):
        return self._prepare("cancellation", cancellation_id)
