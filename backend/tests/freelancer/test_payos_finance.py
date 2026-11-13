"""Real financial writer tests; HTTP uses an explicit test-only transport."""

import hashlib
import hmac
import json
from datetime import timedelta, timezone

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.core.config import settings
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import AppException, ConflictError
from app.models import (
    BankDestination,
    Deliverable,
    EscrowAccount,
    FinanceCounter,
    LedgerJournal,
    LedgerPosting,
    MilestoneFunding,
    MilestoneReview,
    MoneyTransfer,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
    ProviderEvent,
    Settlement,
    TransferAttempt,
    User,
)
from app.services import freelancer_bank_service as banks
from app.services import freelancer_collection_service as collection
from app.services import freelancer_finance_worker as worker
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import ctx, now
from app.services.freelancer_financial_writer import DatabaseFinancePort, confirm_transfer_in_tx
from app.services.freelancer_ledger_service import account, post
from app.services.payos_gateway import PayOSError, PayOSGateway, signature
from tests.freelancer.test_group_c_milestones_deliverables import (
    active_contract_fixtures as _active,
)
from tests.freelancer.test_group_c_milestones_deliverables import db_session as _session


@pytest.fixture
def configured(monkeypatch):
    values = {
        "FREELANCER_FINANCE_ENABLED": True,
        "PAYOS_COLLECTION_ENABLED": True,
        "PAYOS_PAYOUT_ENABLED": True,
        "PAYOS_COLLECTION_CLIENT_ID": "test-client",
        "PAYOS_COLLECTION_API_KEY": "test-api",
        "PAYOS_COLLECTION_CHECKSUM_KEY": "test-collection",
        "PAYOS_COLLECTION_BANK_BIN": "970422",
        "PAYOS_COLLECTION_ACCOUNT_NUMBER": "1234567890",
        "PAYOS_PAYOUT_CLIENT_ID": "test-payout-client",
        "PAYOS_PAYOUT_API_KEY": "test-payout-api",
        "PAYOS_PAYOUT_CHECKSUM_KEY": "test-payout",
        "PAYOS_RETURN_URL": "https://site.example/paid",
        "PAYOS_CANCEL_URL": "https://site.example/cancel",
        "PAYOS_WEBHOOK_URL": "https://api.example/webhook",
        "FREELANCER_BANK_ENCRYPTION_KEY": Fernet.generate_key().decode(),
        "FREELANCER_BANK_FINGERPRINT_KEY": "test-fingerprint-secret-separate-123456789",
    }
    for key, value in values.items():
        monkeypatch.setattr(settings, key, value)


@pytest.fixture
def db_session():
    yield from _session.__wrapped__()


@pytest.fixture
def funded_domain(db_session, configured):
    db = db_session
    f = _active.__wrapped__(db)
    f["ms1"].status = "NOT_FUNDED"
    db.add(FinanceCounter(name="writer", next_value=1000000000))
    db.add(
        User(
            id=901,
            email="finance-admin@example.test",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
    )
    db.commit()
    for uid in (f["client"].id, f["student"].id):
        run_command(
            db,
            lambda uid=uid: banks.add_in_tx(
                db,
                user_id=uid,
                bank_bin="970422",
                account_number="111111" + str(uid),
                account_name="Recipient " + str(uid),
            ),
        )
    return f


def make_order(db, f, key="fund-first"):
    result = run_command(
        db,
        lambda: collection.create_in_tx(
            db, user_id=f["client"].id, milestone_id=f["ms1"].id, key=key
        ),
    )
    return db.get(PaymentOrder, int(result["id"]))


def receipt_data(order, *, amount=None, ref="receipt-one", account_number=None, received=None):
    return {
        "orderCode": order.order_code,
        "paymentLinkId": "link-1",
        "transaction": {
            "reference": ref,
            "amount": order.expected_amount if amount is None else amount,
            "accountNumber": account_number or settings.PAYOS_COLLECTION_ACCOUNT_NUMBER,
            "transactionDateTime": (received or now()).replace(tzinfo=timezone.utc).isoformat(),
        },
    }


def fund(db, f):
    order = make_order(db, f)
    run_command(db, lambda: collection.apply_receipt_in_tx(db, data=receipt_data(order)))
    return order


def prepare_release(db, f):
    fund(db, f)
    d = Deliverable(
        milestone_id=f["ms1"].id,
        submitted_by=f["student"].id,
        submission_no=1,
        note="Complete",
        submitted_at=now(),
    )
    db.add(d)
    db.flush()
    r = MilestoneReview(
        milestone_id=f["ms1"].id,
        deliverable_id=d.id,
        action="ACCEPT",
        reviewed_by=f["client"].id,
        reviewed_at=now(),
    )
    db.add(r)
    f["ms1"].status = "ACCEPTED"
    db.commit()
    result = run_command(
        db,
        lambda: DatabaseFinancePort().prepare_acceptance_settlement_in_tx(
            db, ctx=ctx(f["client"].id), review_id=r.id
        ),
    )
    return db.get(Settlement, result.settlement_id)


def payout_data(transfer, state="SUCCEEDED"):
    return {
        "id": "payout-" + str(transfer.id),
        "referenceId": transfer.provider_reference_id,
        "approvalState": "COMPLETED",
        "transactions": [
            {
                "id": "tx-" + str(transfer.id),
                "referenceId": transfer.provider_reference_id,
                "amount": transfer.amount,
                "toBin": transfer.destination_snapshot["bank_bin"],
                "toAccountNumber": banks.decrypt_snapshot(transfer.destination_snapshot),
                "state": state,
            }
        ],
    }


def assert_balanced(db):
    totals = {}
    for p in db.scalars(select(LedgerPosting)).all():
        totals[p.journal_id] = totals.get(p.journal_id, 0) + (
            p.amount if p.side == "D" else -p.amount
        )
    assert totals and all(x == 0 for x in totals.values())


def test_collection_and_payout_signature_protocols(configured):
    data = {"z": True, "a": "hello world/+", "n": None}
    collection_text = "a=hello world/+&n=&z=true"
    payout_text = "a=hello%20world/%2B&n=&z=true"
    assert (
        signature(data, "secret")
        == hmac.new(b"secret", collection_text.encode(), hashlib.sha256).hexdigest()
    )
    assert (
        signature(data, "secret", payout=True)
        == hmac.new(b"secret", payout_text.encode(), hashlib.sha256).hexdigest()
    )


def test_gateway_headers_signature_and_no_post_retries(configured):
    calls = []

    def respond(request):
        calls.append(request)
        body = json.loads(request.content)
        assert request.headers["x-client-id"] == "test-payout-client"
        assert request.headers["x-idempotency-key"] == "stable"
        assert request.headers["x-signature"] == signature(body, "test-payout", payout=True)
        raise httpx.ReadTimeout("test timeout")

    gateway = PayOSGateway(payout=True, transport=httpx.MockTransport(respond))
    with pytest.raises(PayOSError):
        gateway.create_payout({"referenceId": "stable"}, "stable")
    assert len(calls) == 1


def test_gateway_rejects_tampered_signature(configured):
    gateway = PayOSGateway(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"code": "00", "data": {"orderCode": 1}, "signature": "bad"}
            )
        )
    )
    with pytest.raises(PayOSError, match="signature"):
        gateway.get_order(1)


def test_bank_encryption_verification_and_snapshot_immutability(db_session, funded_domain):
    row = db_session.scalars(select(BankDestination)).first()
    assert "1111111" not in row.account_number_ciphertext
    assert "ciphertext" not in str(banks.public_destination(row))
    assert row.verification_status == "ACTIVE"
    assert row.verification_source == "SELF_DECLARED"
    assert row.verified_by is None and row.verified_at is None


def test_funding_replay_creates_one_receipt_and_balanced_ledger(db_session, funded_domain):
    db, f = db_session, funded_domain
    order = fund(db, f)
    run_command(db, lambda: collection.apply_receipt_in_tx(db, data=receipt_data(order)))
    assert db.query(PaymentTransaction).count() == 1
    assert db.query(MilestoneFunding).count() == 1
    assert db.query(LedgerJournal).count() == 2
    e = db.query(EscrowAccount).one()
    assert e.funded_amount == 1500000 and e.reserved_amount == 0
    assert f["ms1"].status == "FUNDED" and order.status == "PAID"
    assert make_order(db, f).id == order.id
    assert_balanced(db)


@pytest.mark.parametrize(
    "case,reason",
    [("under", "UNDERPAID"), ("over", "OVERPAID"), ("late", "LATE"), ("wrong", "WRONG_ACCOUNT")],
)
def test_anomalous_money_is_recorded_without_escrow(db_session, funded_domain, case, reason):
    db, f = db_session, funded_domain
    order = make_order(db, f)
    options = (
        {"amount": 100}
        if case == "under"
        else {"amount": 2000000}
        if case == "over"
        else {"received": order.expires_at + timedelta(seconds=1)}
        if case == "late"
        else {"account_number": "wrong-account"}
    )
    run_command(db, lambda: collection.apply_receipt_in_tx(db, data=receipt_data(order, **options)))
    assert db.query(PaymentReviewCase).one().reason == reason
    assert db.query(EscrowAccount).count() == 0 and db.query(LedgerJournal).count() == 1
    assert_balanced(db)


def test_underpayments_never_aggregate(db_session, funded_domain):
    db, f = db_session, funded_domain
    order = make_order(db, f)
    for ref in ("first-half", "second-half"):
        run_command(
            db,
            lambda ref=ref: collection.apply_receipt_in_tx(
                db, data=receipt_data(order, amount=750000, ref=ref)
            ),
        )
    assert db.query(MilestoneFunding).count() == 0
    assert db.query(PaymentReviewCase).count() == 2


def test_webhook_probe_and_duplicate_are_durable_without_money(db_session, funded_domain):
    db = db_session
    data = {
        "orderCode": 123,
        "amount": 3000,
        "code": "00",
        "reference": "TF230204212323",
        "paymentLinkId": "124c33293c43417ab7879e14c8d9eb18",
    }
    envelope = {
        "code": "00",
        "success": True,
        "data": data,
        "signature": signature(data, settings.PAYOS_COLLECTION_CHECKSUM_KEY),
    }
    for _ in range(2):
        run_command(db, lambda: collection.store_webhook_in_tx(db, envelope))
    assert db.query(ProviderEvent).one().status == "PROBE"
    assert db.query(LedgerJournal).count() == 0


def test_release_preparation_does_not_recognize_fee_or_disbursement(db_session, funded_domain):
    db, f = db_session, funded_domain
    settlement = prepare_release(db, f)
    assert settlement.fee_amount == 75000 and settlement.net_amount == 1425000
    assert db.query(LedgerJournal).count() == 2
    assert db.query(EscrowAccount).one().reserved_amount == 1500000
    assert f["ms1"].status == "SETTLEMENT_PENDING"
    t = db.query(MoneyTransfer).one()
    run_command(
        db,
        lambda: confirm_transfer_in_tx(db, transfer_id=t.id, payout=payout_data(t, "PROCESSING")),
    )
    assert t.status == "UNKNOWN" and settlement.status != "SUCCEEDED"
    assert db.query(LedgerJournal).count() == 2
    run_command(db, lambda: confirm_transfer_in_tx(db, transfer_id=t.id, payout=payout_data(t)))
    run_command(db, lambda: confirm_transfer_in_tx(db, transfer_id=t.id, payout=payout_data(t)))
    assert t.status == "SUCCEEDED" and settlement.status == "SUCCEEDED"
    assert db.query(LedgerJournal).count() == 4
    assert db.query(EscrowAccount).one().reserved_amount == 0
    assert f["ms1"].status == "PAID_OUT" and f["contract"].status == "ACTIVE"
    assert_balanced(db)


def test_destination_mismatch_cannot_pay_out(db_session, funded_domain):
    db, f = db_session, funded_domain
    prepare_release(db, f)
    t = db.query(MoneyTransfer).one()
    data = payout_data(t)
    data["transactions"][0]["amount"] -= 1
    with pytest.raises(ConflictError):
        run_command(db, lambda: confirm_transfer_in_tx(db, transfer_id=t.id, payout=data))
    assert db.query(EscrowAccount).one().reserved_amount == 1500000
    assert db.query(LedgerJournal).count() == 2


def test_timeout_queries_original_reference_without_reposting(
    db_session, funded_domain, monkeypatch
):
    db, f = db_session, funded_domain
    prepare_release(db, f)
    transfer = db.query(MoneyTransfer).one()
    calls = []

    class Gateway:
        def __init__(self, **kwargs):
            pass

        def balance(self):
            assert not db.in_transaction()
            return {"balance": "99999999", "currency": "VND"}

        def create_payout(self, body, key):
            assert not db.in_transaction()
            calls.append(("POST", body["referenceId"]))
            raise PayOSError("Timeout")

        def find_payout(self, reference):
            assert not db.in_transaction()
            calls.append(("GET", reference))
            return {"payouts": [payout_data(transfer)]}

    monkeypatch.setattr(worker, "PayOSGateway", Gateway)
    with pytest.raises(PayOSError):
        worker.process_transfer(db, transfer_id=transfer.id)
    assert transfer.status == "UNKNOWN" and db.query(EscrowAccount).one().reserved_amount == 1500000
    monkeypatch.setattr(settings, "PAYOS_PAYOUT_ENABLED", False)
    worker.process_transfer(db, transfer_id=transfer.id)
    assert [x[0] for x in calls] == ["POST", "GET"]
    assert calls[0][1] == calls[1][1] and transfer.status == "SUCCEEDED"
    assert db.query(TransferAttempt).count() == 2


def test_low_balance_waits_notifies_and_resumes_without_treasury(db_session, funded_domain, monkeypatch):
    from app.models import Notification, OutboxEvent, TreasuryEntry
    from app.services.freelancer_worker import claim, process_one

    db, f = db_session, funded_domain
    prepare_release(db, f)
    transfer = db.query(MoneyTransfer).one()
    transfer_id = transfer.id
    amount = transfer.amount
    balance = {"balance": amount - 1, "currency": "VND"}
    calls = []
    db.add(User(id=902, email="locked-admin@example.test", role=UserRole.ADMIN, status=UserStatus.LOCKED))
    db.commit()

    class Gateway:
        def __init__(self, **kwargs):
            pass

        def balance(self):
            assert not db.in_transaction()
            return dict(balance)

        def create_payout(self, body, key):
            calls.append(key)
            return payout_data(transfer)

    monkeypatch.setattr(worker, "PayOSGateway", Gateway)
    monkeypatch.setattr(settings, "FREELANCER_WORKER_MAX_ATTEMPTS", 1)
    # Isolate the transfer outbox from collection/notification fixture work.
    outbox = db.scalar(select(OutboxEvent).where(OutboxEvent.event_type == "finance.transfer"))
    outbox_id = outbox.id
    for row in db.scalars(select(OutboxEvent).where(OutboxEvent.id != outbox_id)).all():
        row.status = "SUCCEEDED"
    db.commit()
    for _ in range(3):
        outbox.available_at = now() - timedelta(seconds=1)
        db.commit()
        assert claim(db, OutboxEvent, "test-worker") == outbox_id
        assert not process_one(db, OutboxEvent, outbox_id, "test-worker")
        db.refresh(outbox)
        assert outbox.status == "RETRY"
        assert outbox.last_error == "PAYOUT_BALANCE_REQUIRED"
        assert 0 < (outbox.available_at - now()).total_seconds() <= 60
    assert calls == []
    assert db.query(TransferAttempt).count() == 0
    assert db.get(MoneyTransfer, transfer_id).status == "READY"
    notices = db.scalars(select(Notification).where(Notification.ref_type == "PAYOUT_BALANCE")).all()
    assert len(notices) == 1 and notices[0].user_id == 901
    assert db.query(TreasuryEntry).count() == 0
    # Exactly enough funds is sufficient, and the original queued event resumes.
    balance["balance"] = amount
    outbox.available_at = now() - timedelta(seconds=1)
    db.commit()
    assert claim(db, OutboxEvent, "test-worker") == outbox_id
    assert process_one(db, OutboxEvent, outbox_id, "test-worker")
    assert db.get(MoneyTransfer, transfer_id).status == "SUCCEEDED"
    assert len(calls) == 1
    assert db.query(TreasuryEntry).count() == 0
    assert_balanced(db)


@pytest.mark.parametrize("balance", [None, {}, {"balance": True, "currency": "VND"},
    {"balance": 1500000.5, "currency": "VND"}, {"balance": -1, "currency": "VND"},
    {"balance": "99999999", "currency": "USD"}])
def test_invalid_balance_never_sends_or_marks_insufficient(db_session, funded_domain, monkeypatch, balance):
    from app.models import Notification

    db = db_session
    prepare_release(db, funded_domain)
    transfer_id = db.query(MoneyTransfer).one().id

    class Gateway:
        def __init__(self, **kwargs):
            pass

        def balance(self):
            return balance

        def create_payout(self, *args):
            pytest.fail("Must not send with an invalid provider balance")

    monkeypatch.setattr(worker, "PayOSGateway", Gateway)
    with pytest.raises(AppException) as err:
        worker.process_transfer(db, transfer_id=transfer_id)
    assert err.value.code == "PAYOS_BALANCE_INVALID"
    assert db.query(TransferAttempt).count() == 0
    assert db.scalar(select(Notification.id).where(Notification.ref_type == "PAYOUT_BALANCE")) is None


@pytest.mark.parametrize("threshold,expected_alerts", [(2000000, 1), (1425000, 0)])
def test_low_watermark_warns_without_blocking_affordable_payout(
    db_session, funded_domain, monkeypatch, threshold, expected_alerts
):
    from app.models import Notification

    db = db_session
    prepare_release(db, funded_domain)
    transfer = db.query(MoneyTransfer).one()
    amount, transfer_id = transfer.amount, transfer.id
    calls = []

    class Gateway:
        def __init__(self, **kwargs):
            pass

        def balance(self):
            return {"balance": str(amount), "currency": "VND"}

        def create_payout(self, body, key):
            calls.append(key)
            return payout_data(transfer)

    monkeypatch.setattr(worker, "PayOSGateway", Gateway)
    monkeypatch.setattr(settings, "PAYOS_PAYOUT_LOW_BALANCE_THRESHOLD", threshold)
    worker.process_transfer(db, transfer_id=transfer_id)
    worker.process_transfer(db, transfer_id=transfer_id)
    assert len(calls) == 1
    assert db.get(MoneyTransfer, transfer_id).status == "SUCCEEDED"
    assert db.query(Notification).filter_by(ref_type="PAYOUT_BALANCE").count() == expected_alerts


def test_journal_rejects_unbalanced_and_conflicting_replay(db_session, funded_domain):
    db = db_session

    def write(amount=100):
        a = account(db, "PLATFORM_BANK")
        b = account(db, "UNALLOCATED_RECEIPTS")
        return post(
            db,
            key="unique",
            entity="test",
            entity_id=1,
            lines=[(a.id, "D", amount), (b.id, "C", amount)],
        )

    run_command(db, write)
    with pytest.raises(ConflictError):
        run_command(db, lambda: write(101))

    def bad():
        a = account(db, "PLATFORM_BANK")
        post(db, key="bad", entity="test", entity_id=2, lines=[(a.id, "D", 100), (a.id, "C", 99)])

    with pytest.raises(ValueError):
        run_command(db, bad)


def test_split_consumes_only_successful_leg_and_keeps_other_reserve(db_session, funded_domain):
    from app.models import CancellationAgreement

    db, f = db_session, funded_domain
    fund(db, f)
    cancellation = CancellationAgreement(
        milestone_id=f["ms1"].id,
        requested_by=f["client"].id,
        basis="MUTUAL",
        reason="Both parties agree",
        freelancer_gross=1000000,
        refund_amount=500000,
        terms_hash="a" * 64,
        status="ACCEPTED",
        policy_snapshot={},
        client_accepted_at=now(),
        freelancer_accepted_at=now(),
    )
    db.add(cancellation)
    db.commit()
    result = run_command(
        db,
        lambda: DatabaseFinancePort().prepare_cancellation_settlement_in_tx(
            db, ctx=ctx(f["client"].id), cancellation_id=cancellation.id
        ),
    )
    settlement = db.get(Settlement, result.settlement_id)
    legs = db.scalars(
        select(MoneyTransfer).where(MoneyTransfer.settlement_id == settlement.id)
    ).all()
    release = next(t for t in legs if t.purpose == "RELEASE")
    refund = next(t for t in legs if t.purpose == "REFUND")
    run_command(
        db, lambda: confirm_transfer_in_tx(db, transfer_id=release.id, payout=payout_data(release))
    )
    run_command(
        db,
        lambda: confirm_transfer_in_tx(
            db, transfer_id=refund.id, payout=payout_data(refund, "FAILED")
        ),
    )
    escrow = db.query(EscrowAccount).one()
    assert escrow.reserved_amount == 500000 and escrow.released_gross == 1000000
    assert settlement.status == "PARTIALLY_SUCCEEDED" and cancellation.status == "ACCEPTED"
    assert f["ms1"].status == "SETTLEMENT_PENDING"
    run_command(
        db, lambda: confirm_transfer_in_tx(db, transfer_id=refund.id, payout=payout_data(refund))
    )
    assert escrow.reserved_amount == 0 and escrow.refunded_amount == 500000
    assert settlement.status == "SUCCEEDED" and cancellation.status == "EXECUTED"
    assert f["ms1"].status == "PARTIALLY_RELEASED"
    assert_balanced(db)


def test_disabled_payout_keeps_queries_available(configured, monkeypatch):
    monkeypatch.setattr(settings, "PAYOS_PAYOUT_ENABLED", False)
    data = {"payouts": [], "pagination": {"total": 0}}

    def response(request):
        return httpx.Response(
            200,
            json={"code": "00", "data": data},
            headers={
                "x-signature": signature(data, settings.PAYOS_PAYOUT_CHECKSUM_KEY, payout=True)
            },
        )

    gateway = PayOSGateway(payout=True, transport=httpx.MockTransport(response))
    assert gateway.find_payout("original")["payouts"] == []
    with pytest.raises(PayOSError):
        gateway.create_payout({}, "blocked")


def test_no_receipt_credit_from_browser_return_or_unconfirmed_webhook(
    db_session, funded_domain, monkeypatch
):
    db, f = db_session, funded_domain
    order = make_order(db, f)
    tx = receipt_data(order)["transaction"]
    data = {**tx, "orderCode": order.order_code, "paymentLinkId": "link-1", "code": "00"}
    envelope = {
        "code": "00",
        "success": True,
        "data": data,
        "signature": signature(data, settings.PAYOS_COLLECTION_CHECKSUM_KEY),
    }
    run_command(db, lambda: collection.store_webhook_in_tx(db, envelope))
    e = db.query(ProviderEvent).one()

    class Gateway:
        def get_order(self, code):
            assert not db.in_transaction()
            return {"orderCode": code, "id": "link-1", "transactions": []}

    monkeypatch.setattr(worker, "PayOSGateway", Gateway)
    with pytest.raises(AppException, match="pending"):
        worker.process_receipt(db, event_id=e.id)
    assert db.query(LedgerJournal).count() == 0


def test_env_initializer_preserves_existing_values_and_keys(tmp_path):
    from scripts.configure_payos import initialize

    (tmp_path / ".env.example").write_text(
        "PAYOS_RETURN_URL=\nFREELANCER_BANK_ENCRYPTION_KEY=\nFREELANCER_BANK_FINGERPRINT_KEY=\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "PAYOS_RETURN_URL=https://existing.example/return\n", encoding="utf-8"
    )
    initialize(tmp_path)
    first = (tmp_path / ".env").read_text(encoding="utf-8")
    initialize(tmp_path)
    assert first == (tmp_path / ".env").read_text(encoding="utf-8")
    assert "PAYOS_RETURN_URL=https://existing.example/return" in first


def test_manual_treasury_writes_are_retired():
    from app.routers.freelancer_finance import router

    routes = [(route.path, route.methods) for route in router.routes]
    assert ("/admin/finance/treasury-entries", {"GET"}) in routes
    assert not any("treasury-entries" in path and "POST" in methods for path, methods in routes)


def test_api_finance_is_private_and_serializes_money(db_session, funded_domain, auth_headers):
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.main import app

    db, f = db_session, funded_domain
    order = fund(db, f)

    def get_test_db():
        yield db

    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = get_test_db
    try:
        with TestClient(app) as client:
            url = f"/api/v1/milestones/{f['ms1'].id}/finance"
            response = client.get(url, headers=auth_headers(f["client"]))
            assert response.status_code == 200
            assert response.json()["data"]["funded_amount"] == "1500000"
            assert response.json()["data"]["fee_amount"] == "75000"
            assert response.json()["data"]["net_amount"] == "1425000"
            assert client.get(url, headers=auth_headers(f["outsider"])).status_code == 404
            detail = client.get(
                f"/api/v1/payment-orders/{order.id}", headers=auth_headers(f["client"])
            )
            assert detail.status_code == 200 and "receiving_account_snapshot" not in detail.text
            assert (
                client.post(
                    f"/api/v1/milestones/{f['ms2'].id}/payment-orders",
                    headers=auth_headers(f["client"]),
                ).status_code
                == 422
            )
            assert (
                client.post(
                    "/api/v1/webhooks/payos/collection",
                    json={"code": "00", "success": True, "data": {}, "signature": "bad"},
                ).status_code
                == 401
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_real_outbox_processes_order_then_verified_webhook(db_session, funded_domain, monkeypatch):
    from app.services.freelancer_worker import run_once

    db, f = db_session, funded_domain
    order = make_order(db, f)
    code, amount, order_id = order.order_code, order.expected_amount, order.id
    raw = receipt_data(order)
    transaction = raw["transaction"]
    calls = []

    class Gateway:
        def create_order(self, **kwargs):
            assert not db.in_transaction()
            calls.append("POST")
            return {
                "orderCode": code,
                "amount": amount,
                "bin": "970422",
                "accountNumber": "1234567890",
                "currency": "VND",
                "paymentLinkId": "link-1",
                "checkoutUrl": "https://pay.example/link-1",
                "qrCode": "qr-test-only",
            }

        def get_order(self, code):
            assert not db.in_transaction()
            calls.append("GET")
            return {
                "orderCode": code,
                "id": "link-1",
                "amount": amount,
                "status": "PAID",
                "transactions": [transaction],
            }

    monkeypatch.setattr(worker, "PayOSGateway", Gateway)
    worker.process_order(db, order_id=order_id)
    assert db.get(PaymentOrder, order_id).checkout_url == "https://pay.example/link-1"
    assert db.query(EscrowAccount).count() == 0
    payload = {**transaction, "orderCode": code, "paymentLinkId": "link-1", "code": "00"}
    envelope = {
        "code": "00",
        "success": True,
        "data": payload,
        "signature": signature(payload, settings.PAYOS_COLLECTION_CHECKSUM_KEY),
    }
    run_command(db, lambda: collection.store_webhook_in_tx(db, envelope))
    run_once(db)
    assert db.query(ProviderEvent).one().status == "PROCESSED"
    assert db.query(EscrowAccount).one().funded_amount == amount
    assert calls == ["POST", "GET"]


def test_missing_redirect_configuration_does_not_create_stuck_order(
    db_session, funded_domain, monkeypatch
):
    monkeypatch.setattr(settings, "PAYOS_RETURN_URL", "")
    with pytest.raises(PayOSError):
        make_order(db_session, funded_domain)
    assert db_session.query(PaymentOrder).count() == 0


def test_never_sent_order_can_cancel_without_provider_call(db_session, funded_domain):
    from app.models import DailyLimitReservation, MilestoneFundingGuard

    db, f = db_session, funded_domain
    order = make_order(db, f)
    worker.process_order(db, order_id=order.id, cancel=True)
    assert order.status == "CANCELLED" and f["ms1"].status == "NOT_FUNDED"
    assert db.query(MilestoneFundingGuard).count() == 0
    assert db.query(DailyLimitReservation).filter_by(status="RESERVED").count() == 0


def test_late_create_response_never_downgrades_paid_order(db_session, funded_domain):
    db, f = db_session, funded_domain
    order = fund(db, f)
    response = {
        "orderCode": order.order_code,
        "amount": order.expected_amount,
        "bin": settings.PAYOS_COLLECTION_BANK_BIN,
        "accountNumber": settings.PAYOS_COLLECTION_ACCOUNT_NUMBER,
        "currency": "VND",
        "paymentLinkId": "link-1",
        "checkoutUrl": "https://pay.example/real-link",
        "qrCode": "qr-test-only",
    }
    run_command(
        db,
        lambda: collection.apply_order_query_in_tx(
            db, order_id=order.id, data=response, create_response=True
        ),
    )
    assert order.status == "PAID" and db.query(MilestoneFunding).count() == 1
