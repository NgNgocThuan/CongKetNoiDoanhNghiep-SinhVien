"""The only journal writer. Call under the finance gate; never commit here."""

from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import ConflictError
from app.models import LedgerAccount, LedgerJournal, LedgerPosting
from app.models.freelancer_finance_runtime import FinanceCounter
from app.services.freelancer_domain import lock, now


def finance_gate(db):
    if not settings.FREELANCER_FINANCE_ENABLED:
        return None
    row = lock(db, FinanceCounter, name="writer")
    if not row:
        raise ConflictError(
            "Apply finance migration before enabling money services",
            code="FINANCE_MIGRATION_REQUIRED",
        )
    return row


def next_order_code(db):
    counter = finance_gate(db)
    if counter is None or counter.next_value >= 9007199254740991:
        raise ConflictError("Payment order sequence unavailable")
    value = counter.next_value
    counter.next_value += 1
    db.flush()
    return value


def account(db, kind, *, milestone_id=None, owner_user_id=None):
    code = f"{kind}:{milestone_id or owner_user_id or 'platform'}"
    row = lock(db, LedgerAccount, code=code)
    if row:
        return row
    row = LedgerAccount(
        code=code,
        kind=kind,
        normal_side="D"
        if kind in ("PLATFORM_BANK", "PAYOUT_ACCOUNT", "PROVIDER_FEE_EXPENSE")
        else "C",
        milestone_id=milestone_id,
        owner_user_id=owner_user_id,
    )
    db.add(row)
    db.flush()
    return row


def post(db, *, key, entity, entity_id, lines, actor=None):
    # Reject bools, fractional money, negative/zero lines, and unbalanced entries.
    if len(lines) < 2 or any(
        type(amount) is not int or amount <= 0 or side not in ("D", "C")
        for _, side, amount in lines
    ):
        raise ValueError("Invalid journal lines")
    if sum(amount if side == "D" else -amount for _, side, amount in lines) != 0:
        raise ValueError("Unbalanced journal")
    old = lock(db, LedgerJournal, idempotency_key=key)
    if old:
        existing = db.scalars(
            select(LedgerPosting)
            .where(LedgerPosting.journal_id == old.id)
            .order_by(LedgerPosting.line_no)
        ).all()
        if (
            old.reference_type != entity
            or old.reference_id != entity_id
            or [(x.account_id, str(x.side), x.amount) for x in existing] != lines
        ):
            raise ConflictError(
                "Journal key conflicts with its immutable posting", code="IDEMPOTENCY_CONFLICT"
            )
        return old.id
    row = LedgerJournal(
        reference_type=entity,
        reference_id=entity_id,
        idempotency_key=key,
        description=key,
        posted_at=now(),
        actor_user_id=actor,
    )
    db.add(row)
    db.flush()
    db.add_all(
        [
            LedgerPosting(journal_id=row.id, line_no=i, account_id=ident, side=side, amount=amount)
            for i, (ident, side, amount) in enumerate(lines, 1)
        ]
    )
    db.flush()
    return row.id


def debit_balance(db, account_id):
    rows = db.execute(
        select(LedgerPosting.side, LedgerPosting.amount)
        .where(LedgerPosting.account_id == account_id)
        .with_for_update()
    ).all()
    return sum(amount if side == "D" else -amount for side, amount in rows)
