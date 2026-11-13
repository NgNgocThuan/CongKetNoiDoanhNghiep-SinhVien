"""Financial endpoints. Credentials and bank ciphertext never leave the backend."""

from typing import Annotated, Literal

from fastapi import APIRouter, Header, Query, Request, Response
from pydantic import Field
from sqlalchemy import func, select

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import (
    BankDestination,
    FreelanceContract,
    MoneyTransfer,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
    ReconciliationItem,
    ReconciliationRun,
    Settlement,
    TreasuryEntry,
    User,
)
from app.schemas.freelance_projects import Input, Resource, ResourcePage
from app.schemas.freelancer_disputes import Reason
from app.services import freelancer_bank_service as banks
from app.services import freelancer_collection_service as collection
from app.services import freelancer_finance_admin as operations
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import (
    audit,
    event,
    lock,
    milestone_scope,
    now,
    page,
    party,
    record,
    replay,
)
from app.services.freelancer_finance import get_finance_port
from app.services.payos_gateway import PayOSError, PayOSGateway

router = APIRouter(tags=["Freelancer finance"])
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


class BankCreate(Input):
    bank_bin: str = Field(pattern=r"^\d{6}$")
    account_number: str = Field(pattern=r"^\d{4,30}$")
    account_name: str = Field(min_length=2, max_length=255)


class PaymentReview(Reason):
    action: Literal["ALLOCATE", "RETURN"]


@router.get("/admin/finance/treasury-entries", response_model=ResourcePage)
def treasury_entries(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(db, select(TreasuryEntry).order_by(TreasuryEntry.id.desc()), number, size)


def enabled():
    if not settings.FREELANCER_FINANCE_ENABLED:
        raise AppException("Finance disabled", code="FINANCE_NOT_READY", status_code=503)


def visible_order(db, order_id, user_id):
    row = db.get(PaymentOrder, order_id)
    if not row:
        raise NotFoundError("Payment order not found")
    milestone_scope(db, row.milestone_id, user_id, allow_admin=True)
    return row


@router.post("/bank-destinations", response_model=Resource)
def create_bank(payload: BankCreate, db: DbSession, u: CurrentUser, key: Key):
    enabled()
    return {
        "data": run_command(
            db,
            lambda: replay(
                db,
                actor_id=u.id,
                operation="bank.create",
                key=key,
                body=payload.model_dump(),
                action=lambda: banks.add_in_tx(db, user_id=u.id, **payload.model_dump()),
            ),
        )
    }


@router.get("/bank-destinations", response_model=ResourcePage)
def list_banks(
    db: DbSession, u: CurrentUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(
        db,
        select(BankDestination)
        .where(BankDestination.user_id == u.id)
        .order_by(BankDestination.id.desc()),
        number,
        size,
        project=banks.public_destination,
    )


@router.post("/bank-destinations/{destination_id}/disable", response_model=Resource)
def disable_bank(destination_id: int, payload: Reason, db: DbSession, u: CurrentUser, key: Key):
    enabled()

    def op():
        row = lock(db, BankDestination, id=destination_id)
        if not row or (row.user_id != u.id and u.role != "ADMIN"):
            raise NotFoundError("Bank destination not found")

        def action():
            row.verification_status = "DISABLED"
            audit(
                db,
                u.id,
                "bank_destination.disabled",
                "bank_destinations",
                row.id,
                reason=payload.reason,
            )
            return banks.public_destination(row)

        return replay(
            db,
            actor_id=u.id,
            operation="bank.disable",
            key=key,
            body={"id": destination_id, **payload.model_dump()},
            action=action,
        )

    return {"data": run_command(db, op)}


@router.get("/admin/bank-destinations", response_model=ResourcePage)
def all_banks(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    def view(row):
        from app.models import ClientProfile
        owner = db.get(User, row.user_id)
        client = db.scalar(select(ClientProfile).where(ClientProfile.user_id == row.user_id))
        name = (owner.student.full_name if owner and owner.student else
                owner.company.name if owner and owner.company else
                owner.admin.full_name if owner and owner.admin else
                client.full_name if client else owner.email if owner else "Tài khoản không còn hoạt động")
        labels = {"STUDENT": "Sinh viên", "CLIENT": "Người thuê", "COMPANY": "Doanh nghiệp", "ADMIN": "Quản trị viên"}
        return {**banks.public_destination(row), "user_name": name,
                "user_email": owner.email if owner else None,
                "user_role_label": labels.get(owner.role, "Người dùng") if owner else "Người dùng"}
    return page(
        db,
        select(BankDestination).order_by(BankDestination.id.desc()),
        number,
        size,
        project=view,
    )


@router.post("/milestones/{milestone_id}/payment-orders", response_model=Resource, status_code=202)
def create_order(milestone_id: int, db: DbSession, u: CurrentUser, key: Key):
    enabled()
    order_data = run_command(
        db,
        lambda: collection.create_in_tx(db, user_id=u.id, milestone_id=milestone_id, key=key),
    )
    order_id = int(order_data["id"])
    try:
        from app.services.freelancer_finance_worker import process_order

        process_order(db, order_id=order_id)
        order = db.get(PaymentOrder, order_id)
        if order:
            return {"data": collection.order_public(order)}
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("Synchronous PayOS order creation failed: %s", exc)
    return {"data": order_data}


@router.get("/payment-orders/{order_id}", response_model=Resource)
def get_order(order_id: int, db: DbSession, u: CurrentUser):
    row = visible_order(db, order_id, u.id)
    if row.status in ("CREATING", "PENDING", "PROCESSING", "UNKNOWN"):
        try:
            from app.services.freelancer_finance_worker import process_order

            process_order(db, order_id=row.id)
            db.refresh(row)
        except Exception:
            pass
    return {"data": collection.order_public(row)}


@router.get("/contracts/{contract_id}/payment-orders", response_model=ResourcePage)
def contract_orders(
    contract_id: int,
    db: DbSession,
    u: CurrentUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    from app.models import Milestone

    c = db.get(FreelanceContract, contract_id)
    if not c:
        raise NotFoundError("Contract not found")
    party(db, c, u.id, allow_admin=True)
    return page(
        db,
        select(PaymentOrder)
        .join(Milestone, Milestone.id == PaymentOrder.milestone_id)
        .where(Milestone.contract_id == c.id)
        .order_by(PaymentOrder.id.desc()),
        number,
        size,
        project=collection.order_public,
    )


@router.get("/payment-orders/{order_id}/transactions", response_model=ResourcePage)
def order_transactions(
    order_id: int,
    db: DbSession,
    u: CurrentUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    visible_order(db, order_id, u.id)
    return page(
        db,
        select(PaymentTransaction)
        .where(PaymentTransaction.payment_order_id == order_id)
        .order_by(PaymentTransaction.id.desc()),
        number,
        size,
        project=lambda row: record(row, exclude=("raw_payload_json",)),
    )


@router.get("/settlements/{settlement_id}/money-transfers", response_model=ResourcePage)
def settlement_transfers(
    settlement_id: int,
    db: DbSession,
    u: CurrentUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    row = db.get(Settlement, settlement_id)
    if not row:
        raise NotFoundError("Settlement not found")
    milestone_scope(db, row.milestone_id, u.id, allow_admin=True)
    return page(
        db,
        select(MoneyTransfer)
        .where(MoneyTransfer.settlement_id == row.id)
        .order_by(MoneyTransfer.id),
        number,
        size,
        project=lambda item: record(item, exclude=("destination_snapshot",)),
    )


@router.post("/payment-orders/{order_id}/refresh", response_model=Resource, status_code=202)
def refresh_order(order_id: int, db: DbSession, u: CurrentUser, key: Key):
    enabled()

    def op():
        visible_order(db, order_id, u.id)
        return replay(
            db,
            actor_id=u.id,
            operation="payment.refresh",
            key=key,
            body={"order_id": order_id},
            action=lambda: {"order_id": str(order_id), "refreshed": True},
        )

    res = run_command(db, op)
    try:
        from app.services.freelancer_finance_worker import process_order

        process_order(db, order_id=order_id)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("Manual refresh PayOS query failed: %s", exc)
    order = db.get(PaymentOrder, order_id)
    return {"data": collection.order_public(order) if order else res}


def queue_order(db, order_id, *, cancel=False):
    event(
        db,
        f"order:{order_id}:manual:{now().isoformat()}",
        "finance.order",
        "payment_orders",
        order_id,
        {"order_id": order_id, "cancel": cancel},
    )
    return {"order_id": str(order_id), "queued": True}


@router.post("/payment-orders/{order_id}/cancel", response_model=Resource, status_code=202)
def cancel_order(order_id: int, payload: Reason, db: DbSession, u: CurrentUser, key: Key):
    enabled()

    def op():
        row = visible_order(db, order_id, u.id)
        if row.payer_user_id != u.id:
            raise NotFoundError("Payment order not found")
        return replay(
            db,
            actor_id=u.id,
            operation="payment.cancel",
            key=key,
            body={"order_id": order_id, **payload.model_dump()},
            action=lambda: {"order_id": str(order_id), "cancelled": True},
        )

    res = run_command(db, op)
    try:
        from app.services.freelancer_finance_worker import process_order

        process_order(db, order_id=order_id, cancel=True)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("Manual cancel PayOS order failed: %s", exc)
    order = db.get(PaymentOrder, order_id)
    return {"data": collection.order_public(order) if order else res}


@router.post("/webhooks/payos/collection")
async def collection_webhook(request: Request, db: DbSession):
    enabled()
    # Reject oversized requests before parsing arbitrary JSON.
    body = await request.body()
    if len(body) > 65536:
        raise AppException("Webhook payload too large", status_code=413)
    import json

    try:
        envelope = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise AppException("Invalid JSON") from None
    if not isinstance(envelope, dict):
        raise AppException("Invalid webhook")
    return run_command(db, lambda: collection.store_webhook_in_tx(db, envelope))


@router.get("/milestones/{milestone_id}/finance", response_model=Resource)
def funding(milestone_id: int, db: DbSession, u: CurrentUser):
    milestone_scope(db, milestone_id, u.id, allow_admin=True)
    from dataclasses import asdict

    state = asdict(get_finance_port().get_funding_state(db, milestone_id=milestone_id))
    for name in ("milestone_id", "funded_amount", "held_amount", "reserved_amount"):
        state[name] = str(state[name])
    state["active_hold_ids"] = [str(x) for x in state["active_hold_ids"]]
    from app.services.freelance_contract_service import FreelanceContractService

    terms = FreelanceContractService().get_milestone_financial_terms(db, milestone_id=milestone_id)
    fee = (terms.amount * terms.fee_rate_bp + 5000) // 10000
    state.update(
        terms_amount=str(terms.amount),
        fee_rate_bp=terms.fee_rate_bp,
        fee_amount=str(fee),
        net_amount=str(terms.amount - fee),
    )
    return {"data": state}


@router.get("/contracts/{contract_id}/finance", response_model=Resource)
def contract_finance(contract_id: int, db: DbSession, u: CurrentUser):
    from app.models import EscrowAccount, Milestone

    c = db.get(FreelanceContract, contract_id)
    if not c:
        raise NotFoundError("Contract not found")
    party(db, c, u.id, allow_admin=True)
    rows = db.scalars(
        select(EscrowAccount)
        .join(Milestone, Milestone.id == EscrowAccount.milestone_id)
        .where(Milestone.contract_id == c.id)
    ).all()
    totals = {"funded_amount": 0, "reserved_amount": 0, "released_gross": 0, "refunded_amount": 0}
    for row in rows:
        for name in totals:
            totals[name] += getattr(row, name)
    totals["held_amount"] = (
        totals["funded_amount"] - totals["released_gross"] - totals["refunded_amount"]
    )
    return {"data": {"contract_id": str(c.id), **{k: str(v) for k, v in totals.items()}}}


@router.get("/milestones/{milestone_id}/settlements", response_model=ResourcePage)
def settlements(
    milestone_id: int,
    db: DbSession,
    u: CurrentUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    milestone_scope(db, milestone_id, u.id, allow_admin=True)
    return page(
        db,
        select(Settlement)
        .where(Settlement.milestone_id == milestone_id)
        .order_by(Settlement.id.desc()),
        number,
        size,
    )


@router.get("/money-transfers/{transfer_id}", response_model=Resource)
def transfer(transfer_id: int, db: DbSession, u: CurrentUser):
    row = db.get(MoneyTransfer, transfer_id)
    if not row:
        raise NotFoundError("Transfer not found")
    if row.settlement_id:
        milestone_scope(
            db, db.get(Settlement, row.settlement_id).milestone_id, u.id, allow_admin=True
        )
    elif row.recipient_user_id != u.id and u.role != "ADMIN":
        raise NotFoundError("Transfer not found")
    return {"data": record(row, exclude=("destination_snapshot",))}


@router.get("/admin/payment-reviews", response_model=ResourcePage)
def payment_reviews(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(db, select(PaymentReviewCase).order_by(PaymentReviewCase.id.desc()), number, size)


@router.post("/admin/payment-reviews/{case_id}/resolve", response_model=Resource)
def resolve_review(case_id: int, payload: PaymentReview, db: DbSession, u: AdminUser, key: Key):
    enabled()
    return {
        "data": run_command(
            db,
            lambda: replay(
                db,
                actor_id=u.id,
                operation="receipt.review",
                key=key,
                body={"id": case_id, **payload.model_dump()},
                action=lambda: operations.review_in_tx(
                    db, user_id=u.id, case_id=case_id, **payload.model_dump()
                ),
            ),
        )
    }


@router.post(
    "/admin/money-transfers/{transfer_id}/refresh", response_model=Resource, status_code=202
)
def refresh_transfer(transfer_id: int, payload: Reason, db: DbSession, u: AdminUser, key: Key):
    enabled()

    def op():
        row = lock(db, MoneyTransfer, id=transfer_id)
        if not row:
            raise NotFoundError("Transfer not found")

        def queue():
            event(
                db,
                f"transfer:{transfer_id}:manual:{now().isoformat()}",
                "finance.transfer",
                "money_transfers",
                transfer_id,
                {"transfer_id": transfer_id},
            )
            audit(
                db,
                u.id,
                "transfer.query_requested",
                "money_transfers",
                transfer_id,
                reason=payload.reason,
            )
            return {"queued": True, "transfer_id": str(transfer_id)}

        return replay(
            db,
            actor_id=u.id,
            operation="transfer.query",
            key=key,
            body={"id": transfer_id, **payload.model_dump()},
            action=queue,
        )

    return {"data": run_command(db, op)}


@router.post("/admin/finance/reconciliations", response_model=Resource)
def reconcile(db: DbSession, u: AdminUser, key: Key):
    enabled()
    return {
        "data": run_command(
            db,
            lambda: replay(
                db,
                actor_id=u.id,
                operation="finance.reconcile",
                key=key,
                body={},
                action=lambda: operations.reconcile_in_tx(db, user_id=u.id),
            ),
        )
    }


@router.get("/admin/finance/reconciliations", response_model=ResourcePage)
def runs(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    def view(row):
        data = record(row)
        data["issue_count"] = int((row.summary_json or {}).get("internal_issue_count", 0))
        return data
    return page(db, select(ReconciliationRun).order_by(ReconciliationRun.id.desc()), number, size, project=view)


@router.get("/admin/finance/reconciliations/{run_id}/items", response_model=ResourcePage)
def issues(
    run_id: int,
    db: DbSession,
    u: AdminUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    def view(item):
        from app.models import EscrowAccount, LedgerJournal

        data = record(item)
        milestone_id = None
        if item.entity_type == "money_transfers":
            transfer = db.get(MoneyTransfer, item.entity_id)
            settlement = db.get(Settlement, transfer.settlement_id) if transfer and transfer.settlement_id else None
            milestone_id = settlement.milestone_id if settlement else None
            data.update(amount=str(transfer.amount) if transfer else None,
                        local_status=str(transfer.status) if transfer else None,
                        target_kind="TRANSFER", target_id=str(transfer.id) if transfer else None,
                        settlement_id=str(settlement.id) if settlement else None)
        elif item.entity_type == "escrow_accounts":
            escrow = db.get(EscrowAccount, item.entity_id)
            milestone_id = escrow.milestone_id if escrow else None
            data.update(target_kind="MILESTONE", target_id=str(milestone_id) if milestone_id else None)
        elif item.entity_type == "payment_review_cases":
            case = db.get(PaymentReviewCase, item.entity_id)
            tx = db.get(PaymentTransaction, case.payment_transaction_id) if case else None
            order = db.get(PaymentOrder, tx.payment_order_id) if tx and tx.payment_order_id else None
            milestone_id = order.milestone_id if order else None
            data.update(amount=str(tx.amount) if tx else None,
                        target_kind="RECEIPT", target_id=str(case.id) if case else None)
        elif item.entity_type == "ledger_journals":
            journal = db.get(LedgerJournal, item.entity_id)
            if journal and journal.reference_type == "milestones":
                milestone_id = journal.reference_id
            data.update(target_kind="JOURNAL", target_id=str(item.entity_id))
        data.update(_provider_context(db, milestone_id))
        return data

    return page(
        db,
        select(ReconciliationItem)
        .where(ReconciliationItem.run_id == run_id)
        .order_by(ReconciliationItem.id),
        number,
        size,
        project=view,
    )


def _provider_context(db, milestone_id):
    from app.models import Company, FreelanceProject, Milestone, Student

    milestone = db.get(Milestone, milestone_id) if milestone_id else None
    contract = db.get(FreelanceContract, milestone.contract_id) if milestone else None
    project = db.get(FreelanceProject, contract.project_id) if contract else None
    student = db.get(Student, contract.freelancer_student_id) if contract else None
    company = db.get(Company, contract.company_id) if contract and contract.company_id else None
    client = db.get(User, contract.client_user_id) if contract else None
    return {
        "project_id": str(project.id) if project else None,
        "project_title": project.title if project else None,
        "milestone_id": str(milestone.id) if milestone else None,
        "student_name": student.full_name if student else None,
        "client_name": company.name if company else client.email if client else None,
    }


@router.get("/admin/finance/payos-history", response_model=ResourcePage)
def payos_history(
    db: DbSession,
    u: AdminUser,
    direction: Literal["COLLECTION", "PAYOUT"] = Query(...),
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=20),
):
    """Live, signed PayOS view enriched with local project context."""
    if direction == "PAYOUT":
        offset = (number - 1) * size
        provider = PayOSGateway(payout=True).list_payouts(limit=size, offset=offset)
        raw_rows = provider.get("payouts") or []
        if isinstance(raw_rows, dict):
            raw_rows = list(raw_rows.values())
        pagination = provider.get("pagination") or {}
        items = []
        for payout in raw_rows if isinstance(raw_rows, list) else []:
            reference = payout.get("referenceId")
            transfer = db.scalar(
                select(MoneyTransfer).where(MoneyTransfer.provider_reference_id == reference)
            )
            settlement = db.get(Settlement, transfer.settlement_id) if transfer and transfer.settlement_id else None
            txs = payout.get("transactions") or []
            if isinstance(txs, dict):
                txs = list(txs.values())
            tx = txs[0] if isinstance(txs, list) and txs else {}
            provider_amount = tx.get("amount")
            matched = bool(
                transfer and provider_amount == transfer.amount
                and tx.get("state") == transfer.provider_transaction_state
            )
            items.append({
                "id": payout.get("id") or reference,
                "direction": "PAYOUT", "reference": reference,
                "amount": str(provider_amount or 0),
                "provider_status": tx.get("state") or payout.get("approvalState"),
                "provider_time": payout.get("createdAt"),
                "local_status": str(transfer.status) if transfer else None,
                "match_status": "MATCHED" if matched else "MISMATCH" if transfer else "NOT_IN_SYSTEM",
                **_provider_context(db, settlement.milestone_id if settlement else None),
            })
        total = int(pagination.get("total") or len(items))
    else:
        total = db.scalar(select(func.count()).select_from(PaymentOrder)) or 0
        orders = db.scalars(
            select(PaymentOrder).order_by(PaymentOrder.id.desc()).offset((number - 1) * size).limit(size)
        ).all()
        snapshots = [(o.id, o.order_code, o.milestone_id, o.expected_amount, str(o.status)) for o in orders]
        db.rollback()
        items = []
        gateway = PayOSGateway()
        for order_id, order_code, milestone_id, expected, local_status in snapshots:
            try:
                provider = gateway.get_order(order_code)
            except PayOSError as exc:
                items.append({
                    "id": str(order_id), "direction": "COLLECTION",
                    "reference": str(order_code), "amount": "0",
                    "expected_amount": str(expected), "provider_status": exc.code,
                    "provider_time": None, "local_status": local_status,
                    "match_status": "PROVIDER_UNAVAILABLE",
                    **_provider_context(db, milestone_id),
                })
                continue
            txs = provider.get("transactions") or []
            if isinstance(txs, dict):
                txs = list(txs.values())
            paid = sum(int(tx.get("amount") or 0) for tx in txs if isinstance(tx, dict))
            items.append({
                "id": str(order_id), "direction": "COLLECTION",
                "reference": str(order_code), "amount": str(paid),
                "expected_amount": str(expected), "provider_status": provider.get("status"),
                "provider_time": provider.get("paidAt") or provider.get("createdAt"),
                "local_status": local_status,
                "match_status": "MATCHED" if paid == expected and provider.get("status") == "PAID"
                    else "PENDING" if paid < expected else "MISMATCH",
                **_provider_context(db, milestone_id),
            })
    pages = max(1, (total + size - 1) // size)
    return {"items": items, "total": total, "page": number, "size": size, "pages": pages}


@router.get("/admin/payment-transactions", response_model=ResourcePage)
def all_receipts(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(
        db,
        select(PaymentTransaction).order_by(PaymentTransaction.id.desc()),
        number,
        size,
        project=lambda row: record(row, exclude=("raw_payload_json",)),
    )


@router.get("/admin/payment-transactions/{transaction_id}", response_model=Resource)
def receipt_detail(transaction_id: int, db: DbSession, u: AdminUser):
    row = db.get(PaymentTransaction, transaction_id)
    if not row:
        raise NotFoundError("Payment transaction not found")
    return {"data": record(row, exclude=("raw_payload_json",))}


@router.get("/admin/money-transfers", response_model=ResourcePage)
def all_transfers(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(
        db,
        select(MoneyTransfer).order_by(MoneyTransfer.id.desc()),
        number,
        size,
        project=lambda row: record(row, exclude=("destination_snapshot",)),
    )


@router.get("/admin/finance/readiness", response_model=Resource)
def readiness(db: DbSession, u: AdminUser):
    required = (
        "PAYOS_COLLECTION_CLIENT_ID",
        "PAYOS_COLLECTION_API_KEY",
        "PAYOS_COLLECTION_CHECKSUM_KEY",
        "PAYOS_COLLECTION_BANK_BIN",
        "PAYOS_COLLECTION_ACCOUNT_NUMBER",
        "PAYOS_PAYOUT_CLIENT_ID",
        "PAYOS_PAYOUT_API_KEY",
        "PAYOS_PAYOUT_CHECKSUM_KEY",
        "PAYOS_RETURN_URL",
        "PAYOS_CANCEL_URL",
        "PAYOS_WEBHOOK_URL",
        "FREELANCER_BANK_ENCRYPTION_KEY",
        "FREELANCER_BANK_FINGERPRINT_KEY",
    )
    return {
        "data": {
            "finance_enabled": settings.FREELANCER_FINANCE_ENABLED,
            "collection_enabled": settings.PAYOS_COLLECTION_ENABLED,
            "payout_enabled": settings.PAYOS_PAYOUT_ENABLED,
            "missing_variables": [name for name in required if not getattr(settings, name)],
            "payout_confirmation": "signed transaction SUCCEEDED",
            "webhook_path": settings.API_V1_PREFIX + "/webhooks/payos/collection",
        }
    }


@router.post("/admin/bank-destinations/{destination_id}/verification-data", response_model=Resource)
def bank_verification_data(
    destination_id: int, payload: Reason, response: Response, db: DbSession, u: AdminUser
):
    """Explicit, audited access to the number needed for ownership verification."""

    def operation():
        row = lock(db, BankDestination, id=destination_id)
        if not row:
            raise NotFoundError("Bank destination not found")
        number = banks.decrypt_snapshot(banks.snapshot(row))
        # Never write the account number or ciphertext into the audit payload.
        audit(
            db,
            u.id,
            "bank_destination.inspected",
            "bank_destinations",
            row.id,
            reason=payload.reason,
        )
        return {
            "id": str(row.id),
            "bank_bin": row.bank_bin,
            "account_name": row.account_name,
            "account_number": number,
        }

    data = run_command(db, operation)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return {"data": data}


class BankCatalogItem(Input):
    bin: str
    name: str
    shortName: str
    code: str
    logo: str


@router.get("/finance/banks", response_model=list[BankCatalogItem])
def bank_catalog(_: CurrentUser):
    from app.services.bank_catalog import banks
    return banks()
