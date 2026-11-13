"""Transaction boundary shared by Freelancer modules; no provider calls here."""

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

from app.contracts.freelancer.ports import FinancePort, WorkPort
from app.contracts.freelancer.types import CommandContext, SettlementRef

T = TypeVar("T")


def run_command(db: Session, operation: Callable[[], T]) -> T:
    """Own the request session, including an existing read-only autobegin.

    Call once at the outer boundary. Subservices flush only. A session with
    unrelated pending writes or a nested transaction must not be committed here.
    """
    if db.in_nested_transaction() or db.new or db.dirty or db.deleted:
        raise ValueError("Commands require an exclusive session without pending writes")
    from sqlalchemy.exc import DBAPIError

    for attempt in range(3):
        try:
            from app.services.freelancer_ledger_service import finance_gate

            finance_gate(db)
            result = operation()
            db.commit()
            return result
        except DBAPIError as exc:
            db.rollback()
            code = exc.orig.args[0] if getattr(exc.orig, "args", None) else None
            if code not in (1205, 1213) or attempt == 2:
                raise
        except Exception:
            db.rollback()
            raise
    raise RuntimeError("Unreachable command retry state")


def accept_milestone(
    db: Session,
    *,
    ctx: CommandContext,
    milestone_id: int,
    deliverable_id: int,
    work: WorkPort,
    finance: FinancePort,
    automatic: bool = False,
) -> SettlementRef:
    """Acceptance and settlement creation are atomic, not two committed actions.

    Work implementation must acquire project/contract/milestone locks first.
    Finance rechecks escrow and holds before reserving. No success stub is used.
    """

    def operation() -> SettlementRef:
        review = work.record_acceptance_in_tx(
            db,
            ctx=ctx,
            milestone_id=milestone_id,
            deliverable_id=deliverable_id,
            source="AUTO" if automatic else "MANUAL",
        )
        return finance.prepare_acceptance_settlement_in_tx(db, ctx=ctx, review_id=review.review_id)

    return run_command(db, operation)
