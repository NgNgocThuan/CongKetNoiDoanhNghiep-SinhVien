"""Payment intents and verified receipts. Browser return URLs never fund escrow."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import AppException, ConflictError, NotFoundError
from app.models import (
    Company,
    EscrowAccount,
    MilestoneFunding,
    MilestoneFundingGuard,
    MilestoneHold,
    MoneyTransfer,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
    ProviderEvent,
    Student,
)
from app.services import freelancer_limits as limits
from app.services.freelancer_accounts.eligibility_service import get_client_eligibility
from app.services.freelancer_domain import audit, event, lock, milestone_scope, now, record
from app.services.freelancer_financial_writer import holds, terms
from app.services.freelancer_ledger_service import account, next_order_code, post
from app.services.payos_gateway import PayOSGateway, validate_url, verify_collection_webhook
from app.utils.hashing import sha256_json

ORDER_FIELDS = (
    "id",
    "milestone_id",
    "expected_amount",
    "order_code",
    "status",
    "checkout_url",
    "qr_payload",
    "expires_at",
    "paid_at",
)


def order_public(row):
    data = record(row, fields=ORDER_FIELDS)
    data["order_code"] = str(row.order_code)
    return data


def create_in_tx(db, *, user_id, milestone_id, key):
    PayOSGateway()  # Validate channel configuration before accepting an intent.
    validate_url(settings.PAYOS_RETURN_URL)
    validate_url(settings.PAYOS_CANCEL_URL)
    if not settings.PAYOS_COLLECTION_ENABLED:
        raise AppException("Collection disabled", status_code=503, code="PAYOS_CONFIGURATION")
    if not settings.FREELANCER_FINANCE_ENABLED:
        raise AppException("Finance disabled", status_code=503, code="FINANCE_NOT_READY")
    if not settings.PAYOS_COLLECTION_BANK_BIN or not settings.PAYOS_COLLECTION_ACCOUNT_NUMBER:
        raise AppException(
            "Configure receiving bank account", status_code=503, code="PAYOS_CONFIGURATION"
        )
    p, c, m, escrow = milestone_scope(db, milestone_id, user_id)
    if c.client_user_id != user_id:
        raise NotFoundError("Milestone not found")
    body_hash = sha256_json({"milestone_id": milestone_id})
    old = lock(db, PaymentOrder, payer_user_id=user_id, request_key=key)
    if old:
        if old.request_hash != body_hash:
            raise ConflictError("Payment key conflict", code="IDEMPOTENCY_CONFLICT")
        return order_public(old)
    eligibility = get_client_eligibility(db, user_id=user_id, now_utc=now())
    if not eligibility.can_fund:
        raise ConflictError("Client is not eligible to fund", code="CLIENT_NOT_ELIGIBLE")
    if (
        c.status != "ACTIVE"
        or escrow
        or m.status != "NOT_FUNDED"
        or lock(db, MilestoneFundingGuard, milestone_id=m.id)
    ):
        raise ConflictError("Milestone cannot receive a new payment order")
    holds(db, m.id)
    t = terms(db, m.id)
    order = PaymentOrder(
        milestone_id=m.id,
        payer_user_id=user_id,
        expected_amount=t.amount,
        order_code=next_order_code(db),
        request_key=key,
        request_hash=body_hash,
        receiving_account_snapshot={
            "bank_bin": settings.PAYOS_COLLECTION_BANK_BIN,
            "account_number": settings.PAYOS_COLLECTION_ACCOUNT_NUMBER,
        },
        expires_at=now() + timedelta(seconds=settings.PAYOS_ORDER_TTL_SECONDS),
    )
    db.add(order)
    db.flush()
    limits.reserve(
        db,
        scope="platform:collection",
        limit=settings.FREELANCER_DAILY_COLLECTION_LIMIT,
        amount=t.amount,
        order_id=order.id,
    )
    if c.company_id:
        from app.services.freelancer_policy_service import company_limits

        value = company_limits(db, db.get(Company, c.company_id))
        daily = (
            value.get("max_daily_funding") if isinstance(value, dict) else value.max_daily_funding
        )
        limits.reserve(
            db,
            scope=f"company:{c.company_id}:collection",
            limit=daily,
            amount=t.amount,
            order_id=order.id,
        )
    db.add(MilestoneFundingGuard(milestone_id=m.id, payment_order_id=order.id))
    m.status = "FUNDING_PENDING"
    # Note: PayOS payment order & QR are created synchronously by the caller; no background event queued.
    audit(db, user_id, "payment_order.created", "payment_orders", order.id)
    return order_public(order)


def store_webhook_in_tx(db, envelope):
    data = verify_collection_webhook(envelope)
    external = data.get("reference")
    if (
        not isinstance(external, str)
        or not 1 <= len(external) <= 150
        or type(data.get("orderCode")) is not int
        or type(data.get("amount")) is not int
        or data["amount"] <= 0
    ):
        raise AppException("Invalid webhook receipt", code="PAYOS_EVENT_INVALID")
    channel = settings.PAYOS_COLLECTION_CHANNEL
    digest = sha256_json(data)
    old = lock(db, ProviderEvent, channel_key=channel, event_key=external)
    if old:
        if old.payload_hash != digest:
            raise ConflictError("Conflicting provider event", code="PAYOS_EVENT_CONFLICT")
        return {"accepted": True}
    probe = (
        external == "TF230204212323"
        and data["orderCode"] == 123
        and data.get("paymentLinkId") == "124c33293c43417ab7879e14c8d9eb18"
    )
    row = ProviderEvent(
        channel_key=channel,
        event_key=external,
        event_type="PAYMENT",
        payload_hash=digest,
        payload_json=data,
        status="PROBE" if probe else "RECEIVED",
        available_at=now(),
    )
    db.add(row)
    db.flush()
    if not probe:
        event(
            db,
            f"provider-event:{row.id}",
            "finance.receipt",
            "provider_events",
            row.id,
            {"event_id": row.id},
        )
    return {"accepted": True}


def provider_time(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone(timedelta(hours=7)))
        return result.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, TypeError, AttributeError):
        raise AppException(
            "Provider receipt has invalid timestamp", code="PAYOS_RECEIPT_INVALID"
        ) from None


def apply_receipt_in_tx(db, *, data, provider_event_id=None):
    """data must come from a signed GET, not directly from an inbound webhook."""
    code, tx, link_id = data["orderCode"], data["transaction"], data["paymentLinkId"]
    amount = tx.get("amount")
    if (
        type(amount) is not int
        or amount <= 0
        or not tx.get("reference")
        or not tx.get("accountNumber")
    ):
        raise AppException("Invalid confirmed receipt", code="PAYOS_RECEIPT_INVALID")
    channel = settings.PAYOS_COLLECTION_CHANNEL
    old = lock(db, PaymentTransaction, channel_key=channel, external_ref=tx["reference"])
    if old:
        if old.amount != amount or old.receiving_account_ref != tx["accountNumber"]:
            raise ConflictError("Provider receipt reference conflict")
        return old
    order = lock(db, PaymentOrder, order_code=code)
    mid = order.milestone_id if order else None
    bank = account(db, "PLATFORM_BANK")
    suspense = account(db, "UNALLOCATED_RECEIPTS")
    journal_id = post(
        db,
        key="receipt:" + sha256_json({"channel": channel, "reference": tx["reference"]}),
        entity="provider_events" if provider_event_id else "payment_orders",
        entity_id=provider_event_id or (order.id if order else 0),
        lines=[(bank.id, "D", amount), (suspense.id, "C", amount)],
    )
    receipt = PaymentTransaction(
        payment_order_id=order.id if order else None,
        provider_event_id=provider_event_id,
        channel_key=channel,
        external_ref=tx["reference"],
        amount=amount,
        receiving_account_ref=tx["accountNumber"],
        received_at=provider_time(tx["transactionDateTime"]),
        received_time_raw=tx["transactionDateTime"],
        receipt_journal_id=journal_id,
        raw_payload_json=data,
    )
    db.add(receipt)
    db.flush()
    reason = None
    if not order:
        reason = "UNMATCHED"
    else:
        _, c, m, escrow = milestone_scope(db, mid, None, internal=True)
        if escrow:
            reason = "DUPLICATE_PAYMENT"
        elif (
            tx["accountNumber"].replace(" ", "") not in {
                (order.receiving_account_snapshot.get("account_number") or "").replace(" ", ""),
                (settings.PAYOS_COLLECTION_ACCOUNT_NUMBER or "").replace(" ", ""),
                (tx.get("virtualAccountNumber") or "").replace(" ", ""),
            }
            or (order.payment_link_id and order.payment_link_id != link_id)
        ):
            reason = "WRONG_ACCOUNT"
        elif db.scalar(
            select(MilestoneHold.id).where(
                MilestoneHold.milestone_id == mid, MilestoneHold.released_at.is_(None)
            )
        ):
            reason = "UNMATCHED"
        elif amount != order.expected_amount:
            reason = "UNDERPAID" if amount < order.expected_amount else "OVERPAID"
        elif (
            receipt.received_at > order.expires_at
            or order.status in ("CANCELLED", "EXPIRED")
            or c.status != "ACTIVE"
            or m.status not in ("NOT_FUNDED", "FUNDING_PENDING")
        ):
            reason = "LATE"
    if reason:
        db.add(PaymentReviewCase(payment_transaction_id=receipt.id, reason=reason))
        if order and order.status != "PAID":
            order.status = "NEEDS_REVIEW"
    else:
        allocate_in_tx(db, receipt=receipt, order=order)
    return receipt


def allocate_in_tx(db, *, receipt, order):
    _, c, m, escrow = milestone_scope(db, order.milestone_id, None, internal=True)
    holds(db, m.id)
    if (
        receipt.allocation_status != "UNALLOCATED"
        or escrow
        or receipt.amount != order.expected_amount
        or c.status != "ACTIVE"
        or m.status not in ("NOT_FUNDED", "FUNDING_PENDING")
    ):
        raise ConflictError("Receipt cannot fund this milestone")
    active_transfers = db.scalar(
        select(MoneyTransfer.id).where(MoneyTransfer.payment_transaction_id == receipt.id)
    )
    if active_transfers:
        raise ConflictError("Receipt has a reserved refund")
    escrow_account = account(db, "ESCROW_HELD", milestone_id=m.id)
    journal_id = post(
        db,
        key=f"funding:{m.id}",
        entity="milestones",
        entity_id=m.id,
        lines=[
            (account(db, "UNALLOCATED_RECEIPTS").id, "D", receipt.amount),
            (escrow_account.id, "C", receipt.amount),
        ],
    )
    db.add(
        MilestoneFunding(
            milestone_id=m.id,
            payment_transaction_id=receipt.id,
            amount=receipt.amount,
            funding_journal_id=journal_id,
        )
    )
    db.add(
        EscrowAccount(
            milestone_id=m.id, ledger_account_id=escrow_account.id, funded_amount=receipt.amount
        )
    )
    receipt.allocation_status = "ALLOCATED"
    order.status = "PAID"
    order.paid_at = receipt.received_at
    m.status = "FUNDED"
    guard = lock(db, MilestoneFundingGuard, milestone_id=m.id)
    if guard:
        db.delete(guard)
    limits.finish(db, order_id=order.id, consume=True)
    audit(db, None, "milestone.funded", "milestones", m.id)
    from app.services.freelancer_domain import notify

    recipient = db.get(Student, c.freelancer_student_id)
    if recipient:
        notify(
            db,
            recipient.user_id,
            "Người thuê đã ký quỹ",
            "Khoản ký quỹ đã được xác nhận. Bạn có thể mở công việc và bắt đầu thực hiện.",
            ref_type="FREELANCE_MILESTONE",
            ref_id=m.id,
        )
    db.flush()


def apply_order_query_in_tx(db, *, order_id, data, create_response=False):
    order = lock(db, PaymentOrder, id=order_id)
    if (
        type(data.get("orderCode")) is not int
        or data["orderCode"] != order.order_code
        or data.get("amount") != order.expected_amount
    ):
        raise ConflictError("Provider order mismatch", code="PAYOS_ORDER_MISMATCH")
    if create_response:
        snap = dict(order.receiving_account_snapshot or {})
        if not data.get("accountNumber") or data.get("currency") != "VND":
            raise ConflictError("Receiving account mismatch", code="PAYOS_ORDER_MISMATCH")
        if data.get("bin"):
            snap["bank_bin"] = data["bin"]
        if order.payment_link_id and order.payment_link_id != data.get("paymentLinkId"):
            raise ConflictError("Payment link changed", code="PAYOS_ORDER_MISMATCH")
        snap["account_number"] = data["accountNumber"]
        order.receiving_account_snapshot = snap
        order.payment_link_id = data["paymentLinkId"]
        order.checkout_url = data["checkoutUrl"]
        order.qr_payload = data["qrCode"]
        if order.status in ("CREATING", "PROCESSING", "UNKNOWN"):
            order.status = "PENDING"
    else:
        link = data.get("id")
        if not link or (order.payment_link_id and link != order.payment_link_id):
            raise ConflictError("Provider payment link mismatch", code="PAYOS_ORDER_MISMATCH")
        order.payment_link_id = link
        txs = data.get("transactions")
        if not isinstance(txs, list):
            raise AppException("Provider transactions missing", code="PAYOS_RECEIPT_INVALID")
        for tx in txs:
            apply_receipt_in_tx(
                db, data={"orderCode": order.order_code, "paymentLinkId": link, "transaction": tx}
            )
        receipts = db.scalars(
            select(PaymentTransaction)
            .where(PaymentTransaction.payment_order_id == order.id)
            .with_for_update()
        ).all()
        refundable_done = not receipts or all(r.allocation_status == "RETURNED" for r in receipts)
        if (
            refundable_done
            and data.get("status") in ("CANCELLED", "EXPIRED")
            and order.status != "PAID"
        ):
            order.status = data["status"]
            guard = lock(db, MilestoneFundingGuard, milestone_id=order.milestone_id)
            if guard and guard.payment_order_id == order.id:
                db.delete(guard)
                from app.models import Milestone

                m = lock(db, Milestone, id=order.milestone_id)
                if m.status == "FUNDING_PENDING":
                    m.status = "NOT_FUNDED"
            limits.finish(db, order_id=order.id, consume=False)
        elif not txs and order.status in ("CREATING", "PROCESSING", "UNKNOWN"):
            order.status = "PENDING"
    db.flush()
