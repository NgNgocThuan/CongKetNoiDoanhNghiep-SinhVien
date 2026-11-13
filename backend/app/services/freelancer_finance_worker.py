"""Durable provider I/O: commit intention first, query before any retry.

The regular outbox lease recovers crashes. Once POST could have been sent, all
subsequent attempts are GETs with the same reference; never a fresh transfer.
"""

from datetime import timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import AppException, ConflictError
from app.models import (
    BankDestination,
    DisputeDecision,
    Milestone,
    MilestoneFundingGuard,
    MoneyTransfer,
    Notification,
    PaymentOrder,
    ProviderEvent,
    Settlement,
    TransferAttempt,
    User,
)
from app.services import freelancer_bank_service as banks
from app.services import freelancer_limits as limits
from app.services.freelancer_collection_service import apply_order_query_in_tx, apply_receipt_in_tx
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import event, lock, now
from app.services.freelancer_financial_writer import (
    confirm_transfer_in_tx,
    holds,
    payos_idempotency_key,
)
from app.services.payos_gateway import PayOSGateway, validate_url
from app.utils.hashing import sha256_json


def pending():
    raise AppException(
        "Provider outcome still pending; query again", code="PAYOS_PENDING", status_code=503
    )


def notify_low_balance(db, *, available, transfer):
    """One web alert per active admin per hour, across all pending transfers.

    Called under the finance writer lock. Never infer a deposit from a balance.
    """
    for user_id in db.scalars(
        select(User.id).where(User.role == UserRole.ADMIN, User.status == UserStatus.ACTIVE)
    ).all():
        recent = db.scalar(select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.ref_type == "PAYOUT_BALANCE",
            Notification.created_at >= now() - timedelta(hours=1),
        ).limit(1))
        if recent:
            continue
        shortfall = max(0, transfer.amount - available)
        from app.services.freelancer_domain import notify

        notify(db, user_id, "Số dư ví chi PayOS thấp",
            (
                f"Ví chi còn {available:,} VND. Lệnh #{transfer.id} cần {transfer.amount:,} VND. "
                + (f"Còn thiếu {shortfall:,} VND; lệnh đang chờ nạp tiền. " if shortfall else "")
                + "Admin vui lòng nạp thêm vào ví chi. Không cần tải chứng từ lên hệ thống."
            ),
            ref_type="PAYOUT_BALANCE",
            ref_id=transfer.id,
        )


def process_order(db, *, order_id, cancel=False):
    gateway = PayOSGateway()

    def prepare():
        row = lock(db, PaymentOrder, id=order_id)
        if not row:
            return None
        if row.status == "CREATING" and (cancel or row.expires_at <= now()):
            # CREATING proves this order has never been marked for a POST.
            row.status = "CANCELLED" if cancel else "EXPIRED"
            guard = lock(db, MilestoneFundingGuard, milestone_id=row.milestone_id)
            if guard and guard.payment_order_id == row.id:
                db.delete(guard)
                m = lock(db, Milestone, id=row.milestone_id)
                if m.status == "FUNDING_PENDING":
                    m.status = "NOT_FUNDED"
            limits.finish(db, order_id=row.id, consume=False)
            return None
        create = row.status == "CREATING" and not cancel
        if create:
            if not settings.PAYOS_COLLECTION_ENABLED:
                raise AppException(
                    "New collections disabled", code="PAYOS_CONFIGURATION", status_code=503
                )
            validate_url(settings.PAYOS_RETURN_URL)
            validate_url(settings.PAYOS_CANCEL_URL)
            row.status = "PROCESSING"
        return {
            "code": row.order_code,
            "amount": row.expected_amount,
            "expires": int(row.expires_at.replace(tzinfo=timezone.utc).timestamp()),
            "create": create,
        }

    info = run_command(db, prepare)
    if not info:
        return
    if info["create"]:
        try:
            data = gateway.create_order(
                code=info["code"], amount=info["amount"], expires=info["expires"]
            )
        except Exception:

            def mark_unknown():
                row = lock(db, PaymentOrder, id=order_id)
                if row.status == "PROCESSING":
                    row.status = "UNKNOWN"

            run_command(db, mark_unknown)
            raise
    else:
        data = gateway.get_order(info["code"])
    run_command(
        db,
        lambda: apply_order_query_in_tx(
            db, order_id=order_id, data=data, create_response=info["create"]
        ),
    )
    if cancel and data.get("status") not in ("PAID", "CANCELLED", "EXPIRED"):
        # A cancellation response alone is insufficient: fetch signed transaction history.
        gateway.cancel_order(info["code"])
        data = gateway.get_order(info["code"])
        run_command(db, lambda: apply_order_query_in_tx(db, order_id=order_id, data=data))

    def check():
        row = lock(db, PaymentOrder, id=order_id)
        if row.status in ("PENDING", "PROCESSING", "UNKNOWN"):
            # A new outbox event makes polling durable even after this event completes.
            event(
                db,
                f"order:{order_id}:poll:{now().isoformat()}",
                "finance.order",
                "payment_orders",
                order_id,
                {"order_id": order_id},
                when=now() + timedelta(seconds=60),
            )

    run_command(db, check)


def process_receipt(db, *, event_id):
    row = db.get(ProviderEvent, event_id)
    if not row or row.status in ("PROCESSED", "PROBE"):
        db.rollback()
        return
    payload = dict(row.payload_json)
    db.rollback()
    confirmed = PayOSGateway().get_order(payload["orderCode"])
    txs = confirmed.get("transactions")
    if (
        not isinstance(txs, list)
        or confirmed.get("orderCode") != payload["orderCode"]
        or confirmed.get("id") != payload.get("paymentLinkId")
    ):
        raise ConflictError("Webhook and queried order disagree", code="PAYOS_RECEIPT_INVALID")
    matched = [tx for tx in txs if tx.get("reference") == payload["reference"]]
    if (
        len(matched) != 1
        or matched[0].get("amount") != payload["amount"]
        or matched[0].get("accountNumber") != payload.get("accountNumber")
    ):
        pending()

    def apply():
        current = lock(db, ProviderEvent, id=event_id)
        if current.status != "PROCESSED":
            apply_receipt_in_tx(
                db,
                provider_event_id=current.id,
                data={
                    "orderCode": payload["orderCode"],
                    "paymentLinkId": confirmed["id"],
                    "transaction": matched[0],
                },
            )
            current.status = "PROCESSED"
            current.processed_at = now()

    run_command(db, apply)


def process_transfer(db, *, transfer_id):
    # No transaction is held during balance/HTTP access.
    initial = db.get(MoneyTransfer, transfer_id)
    if initial and initial.status == "WAITING_BANK":
        db.rollback()
        return
    gateway = PayOSGateway(payout=True)
    initial_attempts = (
        db.scalars(
            select(TransferAttempt)
            .where(TransferAttempt.transfer_id == transfer_id)
            .order_by(TransferAttempt.attempt_no.desc())
        ).all()
        if initial
        else []
    )
    initial_old = initial_attempts[0] if initial_attempts else None
    initial_create = next(
        (attempt for attempt in initial_attempts if attempt.operation == "CREATE"), None
    )
    rejected_create_can_retry = bool(
        initial_old
        and initial_old.operation == "QUERY"
        and initial_old.error_code == "PAYOS_PAYOUT_NOT_FOUND"
        and initial_create
        and initial_create.error_code == "PAYOS_NOT_CONFIRMED"
        and isinstance(initial_create.provider_response_json, dict)
        and initial_create.provider_response_json.get("provider_code") == "605"
    )
    needs_balance = bool(
        initial
        and (
            (initial.status == "READY" and not initial_attempts)
            or rejected_create_can_retry
        )
    )
    db.rollback()
    balance = gateway.balance() if needs_balance else None

    def prepare():
        transfer = lock(db, MoneyTransfer, id=transfer_id)
        if not transfer or transfer.status in ("SUCCEEDED", "WAITING_BANK", "CANCELLED"):
            return None
        attempts = db.scalars(
            select(TransferAttempt)
            .where(TransferAttempt.transfer_id == transfer.id)
            .order_by(TransferAttempt.attempt_no.desc())
            .with_for_update()
        ).all()
        old = attempts[0] if attempts else None
        # A prior POST explicitly rejected by PayOS (e.g. invalid idempotency
        # key) is safe to recreate only after a provider lookup confirms that
        # the stable reference was not created. Keep the attempt history.
        latest_create = next(
            (attempt for attempt in attempts if attempt.operation == "CREATE"), None
        )
        prior_create_rejected = bool(
            old
            and old.operation == "QUERY"
            and old.error_code == "PAYOS_PAYOUT_NOT_FOUND"
            and latest_create
            and latest_create.error_code == "PAYOS_NOT_CONFIRMED"
            and isinstance(latest_create.provider_response_json, dict)
            and latest_create.provider_response_json.get("provider_code") == "605"
        )
        create = (old is None and transfer.status == "READY") or prior_create_rejected
        if create:
            if not settings.PAYOS_PAYOUT_ENABLED:
                raise AppException(
                    "New payouts disabled", code="PAYOS_CONFIGURATION", status_code=503
                )
            try:
                raw_balance = balance["balance"] if isinstance(balance, dict) else None
                if type(raw_balance) not in (int, str) or not str(raw_balance).isdigit():
                    raise ValueError("Expected nonnegative integer VND")
                available = int(raw_balance)
            except (ValueError, KeyError, TypeError):
                raise AppException(
                    "Payout balance unavailable", code="PAYOS_BALANCE_INVALID"
                ) from None
            if not balance or balance.get("currency") != "VND" or available < 0:
                raise AppException("Payout balance invalid", code="PAYOS_BALANCE_INVALID")
            if available < max(transfer.amount, settings.PAYOS_PAYOUT_LOW_BALANCE_THRESHOLD):
                notify_low_balance(db, available=available, transfer=transfer)
            if available < transfer.amount:
                # Commit the notification before raising; no attempt or send intention exists.
                return {"waiting_for_balance": True}
            expected_key = payos_idempotency_key(transfer.provider_reference_id)
            if transfer.idempotency_key != expected_key:
                transfer.idempotency_key = expected_key
            dest = db.get(BankDestination, transfer.destination_id)
            if not dest or dest.verification_status not in banks.USABLE:
                raise ConflictError("Recipient bank destination is disabled")
            if transfer.settlement_id:
                s = db.get(Settlement, transfer.settlement_id)
                decision = (
                    db.get(DisputeDecision, s.source_decision_id) if s.source_decision_id else None
                )
                holds(db, s.milestone_id, allowed_dispute=decision.dispute_id if decision else None)
            limits.prepare_send_day(
                db,
                transfer_id=transfer.id,
                amount=transfer.amount,
                limit=settings.FREELANCER_DAILY_PAYOUT_LIMIT,
            )
        body = {
            "referenceId": transfer.provider_reference_id,
            "amount": transfer.amount,
            "description": "StudentConnect",
            "toBin": transfer.destination_snapshot["bank_bin"],
            "toAccountNumber": banks.decrypt_snapshot(transfer.destination_snapshot),
        }
        attempt = TransferAttempt(
            transfer_id=transfer.id,
            attempt_no=(old.attempt_no + 1) if old else 1,
            operation="CREATE" if create else "QUERY",
            request_hash=sha256_json(body),
            started_at=now(),
        )
        db.add(attempt)
        transfer.status = "PROCESSING" if create else "UNKNOWN"
        if transfer.settlement_id:
            s = lock(db, Settlement, id=transfer.settlement_id)
            if s.status == "PREPARED":
                s.status = "PROCESSING"
        db.flush()
        return {
            "attempt_id": attempt.id,
            "create": create,
            "body": body,
            "key": transfer.idempotency_key,
        }

    info = run_command(db, prepare)
    if info is None:
        return
    if info.get("waiting_for_balance"):
        raise ConflictError(
            "Fund the payout channel before disbursement", code="PAYOUT_BALANCE_REQUIRED"
        )
    try:
        if info["create"]:
            data = gateway.create_payout(info["body"], info["key"])
        else:
            response = gateway.find_payout(info["body"]["referenceId"])
            payouts = response.get("payouts")
            if not isinstance(payouts, list):
                pending()
            matches = [p for p in payouts if p.get("referenceId") == info["body"]["referenceId"]]
            if not matches:
                raise AppException("Payout reference not found; reconcile with provider before resending",
                                   code="PAYOS_PAYOUT_NOT_FOUND", status_code=503)
            if len(matches) != 1:
                pending()
            data = matches[0]

        def apply():
            confirm_transfer_in_tx(db, transfer_id=transfer_id, payout=data)
            t = lock(db, MoneyTransfer, id=transfer_id)
            a = lock(db, TransferAttempt, id=info["attempt_id"])
            a.status = (
                "CONFIRMED_SUCCESS"
                if t.status == "SUCCEEDED"
                else "CONFIRMED_FAILURE"
                if t.status == "FAILED"
                else "UNKNOWN"
            )
            # Avoid persisting full bank account numbers from provider replies.
            a.provider_response_json = {
                "id": data.get("id"),
                "approvalState": data.get("approvalState"),
                "transactionState": t.provider_transaction_state,
            }
            a.finished_at = now()
            a.next_check_at = None if t.status == "SUCCEEDED" else now() + timedelta(seconds=60)
            return t.status

        status = run_command(db, apply)
    except Exception as exc:
        error_code = exc.code if isinstance(exc, AppException) else type(exc).__name__
        diagnostics = getattr(exc, "diagnostics", None)

        def unknown():
            t = lock(db, MoneyTransfer, id=transfer_id)
            if t.status != "SUCCEEDED":
                t.status = "UNKNOWN"
            a = lock(db, TransferAttempt, id=info["attempt_id"])
            a.status = "UNKNOWN"
            a.error_code = error_code
            if diagnostics:
                a.provider_response_json = diagnostics
            a.finished_at = now()
            a.next_check_at = now() + timedelta(seconds=60)

        run_command(db, unknown)
        raise
    if status != "SUCCEEDED":
        pending()


def dispatch(db, kind, data):
    if not settings.FREELANCER_FINANCE_ENABLED:
        raise AppException("Finance disabled", code="FINANCE_NOT_READY", status_code=503)
    if kind == "finance.order":
        process_order(db, order_id=data["order_id"], cancel=data.get("cancel", False))
    elif kind == "finance.receipt":
        process_receipt(db, event_id=data["event_id"])
    elif kind == "finance.transfer":
        process_transfer(db, transfer_id=data["transfer_id"])
    else:
        raise ValueError("Unsupported financial event")
