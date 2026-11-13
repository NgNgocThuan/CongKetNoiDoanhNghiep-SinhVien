"""Review and reconciliation operations; no silent balance corrections."""

from datetime import timedelta

from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError
from app.models import (
    EscrowAccount,
    LedgerJournal,
    LedgerPosting,
    MoneyTransfer,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
    ReconciliationItem,
    ReconciliationRun,
    Settlement,
)
from app.services.freelancer_collection_service import allocate_in_tx
from app.services.freelancer_domain import admin, audit, event, lock, now, record
from app.services.freelancer_financial_writer import DatabaseFinancePort


def review_in_tx(db, *, user_id, case_id, action, reason):
    admin(db, user_id)
    case = lock(db, PaymentReviewCase, id=case_id)
    if not case:
        raise NotFoundError("Payment review not found")
    if case.status == "RESOLVED":
        raise ConflictError("Payment review already resolved")
    receipt = lock(db, PaymentTransaction, id=case.payment_transaction_id)
    order = (
        lock(db, PaymentOrder, id=receipt.payment_order_id) if receipt.payment_order_id else None
    )
    if not order:
        raise ConflictError(
            "Unmatched receipts require provider reconciliation before assigning a beneficiary"
        )
    if action == "ALLOCATE":
        allocate_in_tx(db, receipt=receipt, order=order)
        case.status = "RESOLVED"
        case.resolution = "ALLOCATE"
        case.resolved_at = now()
        case.resolved_by = user_id
    else:
        if receipt.allocation_status != "UNALLOCATED":
            raise ConflictError("Receipt is not available for refund")
        existing = db.scalar(
            select(MoneyTransfer.id)
            .where(MoneyTransfer.payment_transaction_id == receipt.id)
            .with_for_update()
        )
        if existing:
            raise ConflictError("A refund transfer already exists")
        DatabaseFinancePort().create_transfer(
            db,
            transaction_id=receipt.id,
            purpose="UNALLOCATED_REFUND",
            user_id=order.payer_user_id,
            amount=receipt.amount,
        )
        case.status = "UNDER_REVIEW"
        case.resolution = "RETURN"
    case.note = reason
    audit(
        db,
        user_id,
        "payment_review." + action.lower(),
        "payment_review_cases",
        case.id,
        reason=reason,
    )
    return record(case)


def reconcile_in_tx(db, *, user_id):
    admin(db, user_id)
    at = now()
    run = ReconciliationRun(period_from=at - timedelta(days=1), period_until=at, started_at=at)
    db.add(run)
    db.flush()
    count = 0

    def issue(entity, ident, kind, expected=None, actual=None):
        nonlocal count
        count += 1
        db.add(
            ReconciliationItem(
                run_id=run.id,
                issue_key=f"{entity}:{ident}:{kind}",
                entity_type=entity,
                entity_id=ident,
                issue_type=kind,
                expected_amount=expected,
                actual_amount=actual,
                details_json={},
            )
        )

    postings = db.execute(
        select(
            LedgerPosting.journal_id,
            LedgerPosting.account_id,
            LedgerPosting.side,
            LedgerPosting.amount,
        )
    ).all()
    journal_totals, credits = {}, {}
    for jid, aid, side, amount in postings:
        journal_totals[jid] = journal_totals.get(jid, 0) + (amount if side == "D" else -amount)
        credits[aid] = credits.get(aid, 0) + (amount if side == "C" else -amount)
    for jid in db.scalars(select(LedgerJournal.id)).all():
        if jid not in journal_totals or journal_totals[jid] != 0:
            issue("ledger_journals", jid, "UNBALANCED_JOURNAL")
    for escrow in db.scalars(select(EscrowAccount).with_for_update()).all():
        expected = escrow.funded_amount - escrow.released_gross - escrow.refunded_amount
        actual = credits.get(escrow.ledger_account_id, 0)
        if expected != actual:
            issue("escrow_accounts", escrow.id, "ESCROW_LEDGER_MISMATCH", expected, max(0, actual))
        settlements = db.scalars(
            select(Settlement)
            .where(Settlement.milestone_id == escrow.milestone_id)
            .with_for_update()
        ).all()
        reserved = (
            sum(
                s.amount
                for s in settlements
                if s.status in ("PREPARED", "PROCESSING", "PARTIALLY_SUCCEEDED", "FAILED")
            )
            - escrow.released_gross
            - escrow.refunded_amount
        )
        if max(0, reserved) != escrow.reserved_amount:
            issue(
                "escrow_accounts",
                escrow.id,
                "RESERVATION_MISMATCH",
                max(0, reserved),
                escrow.reserved_amount,
            )
    orders = db.scalars(
        select(PaymentOrder)
        .where(PaymentOrder.status.not_in(("CANCELLED", "EXPIRED", "FAILED")))
        .with_for_update()
    ).all()
    for order in orders:
        event(
            db,
            f"recon:{run.id}:order:{order.id}",
            "finance.order",
            "payment_orders",
            order.id,
            {"order_id": order.id},
        )
    for transfer in db.scalars(
        select(MoneyTransfer)
        .where(MoneyTransfer.status.not_in(("SUCCEEDED", "CANCELLED")))
        .with_for_update()
    ).all():
        event(
            db,
            f"recon:{run.id}:transfer:{transfer.id}",
            "finance.transfer",
            "money_transfers",
            transfer.id,
            {"transfer_id": transfer.id},
        )
        if transfer.status in ("UNKNOWN", "FAILED"):
            issue("money_transfers", transfer.id, "PAYOUT_UNRESOLVED")
    for case in db.scalars(
        select(PaymentReviewCase).where(PaymentReviewCase.status != "RESOLVED")
    ).all():
        issue("payment_review_cases", case.id, "RECEIPT_REQUIRES_REVIEW")
    run.status = "SUCCEEDED"
    run.finished_at = now()
    run.summary_json = {
        "internal_issue_count": count,
        "provider_queries_queued": True,
        "scope": "internal ledger and unresolved provider obligations; bank statement reconciliation remains required",
    }
    audit(db, user_id, "finance.reconciliation", "reconciliation_runs", run.id)
    db.flush()
    return record(run)
