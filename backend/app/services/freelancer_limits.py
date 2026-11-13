"""Reserve daily limits before the provider call; UNKNOWN never releases them."""

from datetime import timedelta

from sqlalchemy import select

from app.core.exceptions import ConflictError
from app.models import DailyLimitBucket, DailyLimitReservation
from app.services.freelancer_domain import lock, now


def reserve(db, *, scope, limit, amount, order_id=None, transfer_id=None):
    day = (now() + timedelta(hours=7)).date()
    bucket = lock(db, DailyLimitBucket, scope_key=scope, local_date=day)
    if bucket is None:
        bucket = DailyLimitBucket(
            scope_key=scope,
            local_date=day,
            limit_amount=limit,
            reserved_amount=0,
            consumed_amount=0,
        )
        db.add(bucket)
        db.flush()
    # A lowered policy takes effect immediately, without violating the stored check.
    if bucket.reserved_amount + bucket.consumed_amount + amount > min(limit, bucket.limit_amount):
        raise ConflictError("Daily financial limit reached", code="DAILY_LIMIT_EXCEEDED")
    bucket.reserved_amount += amount
    db.add(
        DailyLimitReservation(
            bucket_id=bucket.id,
            payment_order_id=order_id,
            money_transfer_id=transfer_id,
            amount=amount,
        )
    )
    db.flush()


def finish(db, *, order_id=None, transfer_id=None, consume):
    stmt = select(DailyLimitReservation).where(DailyLimitReservation.status == "RESERVED")
    stmt = (
        stmt.where(DailyLimitReservation.payment_order_id == order_id)
        if order_id is not None
        else stmt.where(DailyLimitReservation.money_transfer_id == transfer_id)
    )
    for row in db.scalars(stmt.with_for_update()).all():
        bucket = lock(db, DailyLimitBucket, id=row.bucket_id)
        bucket.reserved_amount -= row.amount
        if consume:
            bucket.consumed_amount += row.amount
            row.status = "CONSUMED"
            row.consumed_at = now()
        else:
            row.status = "RELEASED"
            row.released_at = now()


def prepare_send_day(db, *, transfer_id, amount, limit):
    """Only before the very first POST; UNKNOWN keeps its original send-day bucket."""
    day = (now() + timedelta(hours=7)).date()
    rows = db.scalars(
        select(DailyLimitReservation)
        .where(
            DailyLimitReservation.money_transfer_id == transfer_id,
            DailyLimitReservation.status == "RESERVED",
        )
        .with_for_update()
    ).all()
    if any(db.get(DailyLimitBucket, row.bucket_id).local_date != day for row in rows):
        finish(db, transfer_id=transfer_id, consume=False)
        reserve(db, scope="platform:payout", limit=limit, amount=amount, transfer_id=transfer_id)
