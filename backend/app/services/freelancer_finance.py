"""Fail closed until the project owner supplies the real financial writer."""

from app.core.exceptions import AppException


class FinanceNotReadyError(AppException):
    status_code = 503
    code = "FINANCE_NOT_READY"


class UnavailableFinancePort:
    """No simulated funding, reserve, ledger entries or payout success."""

    def _unavailable(self):
        raise FinanceNotReadyError("Freelancer financial services are not configured")

    def get_funding_state(self, db, *, milestone_id):
        return self._unavailable()

    def assert_can_start_in_tx(self, db, *, ctx, milestone_id):
        self._unavailable()

    def assert_disputable_in_tx(self, db, *, ctx, milestone_id):
        self._unavailable()

    def prepare_acceptance_settlement_in_tx(self, db, *, ctx, review_id):
        return self._unavailable()

    def prepare_decision_settlement_in_tx(self, db, *, ctx, decision_id):
        return self._unavailable()

    def prepare_cancellation_settlement_in_tx(self, db, *, ctx, cancellation_id):
        return self._unavailable()


def get_finance_port():
    """Explicit factory; missing provider configuration never enables a fake."""
    from app.core.config import settings

    if settings.FREELANCER_FINANCE_ENABLED:
        from app.services.freelancer_financial_writer import DatabaseFinancePort

        return DatabaseFinancePort()
    return UnavailableFinancePort()
