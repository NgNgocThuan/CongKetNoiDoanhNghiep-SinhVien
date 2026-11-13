from types import SimpleNamespace
from unittest.mock import Mock

from sqlalchemy import select

from app.models import (
    BankDestination,
    EscrowAccount,
    MoneyTransfer,
    Notification,
    OutboxEvent,
    Settlement,
    TransferAttempt,
)
from app.services import freelancer_bank_service as banks
from app.services import freelancer_finance_worker as worker
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import ctx
from app.services.freelancer_financial_writer import DatabaseFinancePort
from tests.freelancer.test_payos_finance import (
    configured as configured,
)
from tests.freelancer.test_payos_finance import (  # noqa: F401 (pytest fixture registration)
    db_session as db_session,
)
from tests.freelancer.test_payos_finance import (
    funded_domain as funded_domain,
)
from tests.freelancer.test_payos_finance import (
    payout_data,
    prepare_release,
)


def test_waiting_release_notifies_then_resumes_original_transfer_once(db_session, funded_domain, monkeypatch):
    db, f = db_session, funded_domain
    uid = f["student"].id
    for bank in db.scalars(select(BankDestination).where(BankDestination.user_id == uid)):
        bank.verification_status = "DISABLED"
    db.commit()
    settlement = prepare_release(db, f)
    transfer = db.scalar(select(MoneyTransfer).where(MoneyTransfer.settlement_id == settlement.id))
    assert transfer.status == "WAITING_BANK" and transfer.destination_id is None
    assert settlement.status == "PREPARED"
    assert db.scalar(select(EscrowAccount.reserved_amount)) == settlement.amount
    notice = db.scalar(select(Notification).where(Notification.user_id == uid, Notification.ref_type == "BANK_DESTINATION"))
    assert notice and "ngân hàng" in notice.title
    assert db.scalar(select(OutboxEvent.id).where(OutboxEvent.event_key == f"transfer:{transfer.id}:send")) is None
    gateway = Mock(side_effect=AssertionError("No provider access before bank details"))
    monkeypatch.setattr(worker, "PayOSGateway", gateway)
    worker.process_transfer(db, transfer_id=transfer.id)
    gateway.assert_not_called()

    original_reference, original_key = transfer.provider_reference_id, transfer.idempotency_key
    run_command(db, lambda: DatabaseFinancePort().prepare_acceptance_settlement_in_tx(db, ctx=ctx(f["client"].id), review_id=settlement.source_review_id))
    assert db.query(MoneyTransfer).count() == 1
    assert db.query(Notification).filter_by(user_id=uid, ref_type="BANK_DESTINATION").count() == 1
    body = dict(user_id=uid, bank_bin="970422", account_number="999900001", account_name="STUDENT NAME")
    bank = run_command(db, lambda: banks.add_in_tx(db, **body))
    assert bank["verification_status"] == "ACTIVE"
    db.refresh(transfer)
    assert transfer.status == "READY" and transfer.destination_id == int(bank["id"])
    assert (transfer.provider_reference_id, transfer.idempotency_key) == (original_reference, original_key)
    assert db.query(TransferAttempt).count() == 0
    assert db.query(OutboxEvent).filter_by(event_key=f"transfer:{transfer.id}:send").count() == 1
    run_command(db, lambda: banks.add_in_tx(db, **body))
    frozen = dict(transfer.destination_snapshot)
    run_command(db, lambda: banks.add_in_tx(db, user_id=uid, bank_bin="970422", account_number="999900002", account_name="SECOND BANK"))
    db.refresh(transfer)
    assert transfer.destination_snapshot == frozen
    assert db.query(MoneyTransfer).count() == 1
    assert db.query(OutboxEvent).filter_by(event_key=f"transfer:{transfer.id}:send").count() == 1
    fake = SimpleNamespace(balance=Mock(return_value={"balance": 1000000000, "currency": "VND"}),
                           create_payout=Mock(side_effect=lambda body, key: payout_data(transfer)))
    monkeypatch.setattr(worker, "PayOSGateway", lambda **kwargs: fake)
    worker.process_transfer(db, transfer_id=transfer.id)
    db.refresh(transfer)
    assert transfer.status == "SUCCEEDED"
    assert db.get(Settlement, settlement.id).status == "SUCCEEDED"
    worker.process_transfer(db, transfer_id=transfer.id)
    assert fake.create_payout.call_count == 1


def test_waiting_refund_resumes_for_client_not_other_user(db_session, funded_domain):
    from app.models import PaymentTransaction
    db, f = db_session, funded_domain
    from app.services import freelancer_collection_service as collection
    from tests.freelancer.test_payos_finance import make_order, receipt_data
    order = make_order(db, f)
    run_command(db, lambda: collection.apply_receipt_in_tx(db, data=receipt_data(order, amount=order.expected_amount + 100)))
    receipt = db.query(PaymentTransaction).one()
    uid = f["client"].id
    for bank in db.scalars(select(BankDestination).where(BankDestination.user_id == uid)):
        bank.verification_status = "DISABLED"
    db.commit()
    transfer_id = run_command(db, lambda: DatabaseFinancePort().create_transfer(db, transaction_id=receipt.id, purpose="UNALLOCATED_REFUND", user_id=uid, amount=receipt.amount).id)
    transfer = db.get(MoneyTransfer, transfer_id)
    assert transfer.status == "WAITING_BANK"
    run_command(db, lambda: banks.add_in_tx(db, user_id=f["student"].id, bank_bin="970422", account_number="888880001", account_name="OTHER USER"))
    db.refresh(transfer)
    assert transfer.status == "WAITING_BANK"
    run_command(db, lambda: banks.add_in_tx(db, user_id=uid, bank_bin="970422", account_number="888880002", account_name="CLIENT USER"))
    db.refresh(transfer)
    assert transfer.status == "READY"
    assert db.get(BankDestination, transfer.destination_id).user_id == uid


def test_bank_api_adds_without_review_and_admin_sees_account_owner(db_session, funded_domain):
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import app
    from app.models import Student

    db, f = db_session, funded_domain
    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    student_headers = {"Authorization": "Bearer " + create_access_token(f["student"].id, "STUDENT"), "Idempotency-Key": "self-bank-api"}
    admin_headers = {"Authorization": "Bearer " + create_access_token(901, "ADMIN"), "Idempotency-Key": "admin-disable-bank"}
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/bank-destinations", headers=student_headers,
                                   json={"bank_bin": "970422", "account_number": "777770001", "account_name": "STUDENT NAME"})
            assert response.status_code == 200, response.text
            bank = response.json()["data"]
            assert bank["verification_status"] == "ACTIVE"
            assert bank["status_label"] == "Đang sử dụng"
            destination_id = int(bank["id"])
            response = client.get("/api/v1/admin/bank-destinations", headers=admin_headers)
            assert response.status_code == 200, response.text
            item = next(row for row in response.json()["items"] if int(row["id"]) == destination_id)
            assert item["user_role_label"] == "Sinh viên"
            assert item["user_name"] == db.scalar(select(Student.full_name).where(Student.user_id == f["student"].id))
            assert "ciphertext" not in response.text and "777770001" not in response.text
            assert client.post(f"/api/v1/admin/bank-destinations/{destination_id}/review", headers=admin_headers,
                               json={"approve": True}).status_code == 404
            response = client.post(f"/api/v1/bank-destinations/{destination_id}/disable", headers=admin_headers, json={"reason": "Account issue reported"})
            assert response.status_code == 200, response.text
            assert response.json()["data"]["verification_status"] == "DISABLED"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_split_waits_for_only_missing_refund_bank_and_preserves_successful_release(db_session, funded_domain):
    from app.models import CancellationAgreement
    from app.services.freelancer_domain import now
    from app.services.freelancer_financial_writer import confirm_transfer_in_tx
    from tests.freelancer.test_payos_finance import assert_balanced, fund

    db, f = db_session, funded_domain
    fund(db, f)
    for bank in db.scalars(select(BankDestination).where(BankDestination.user_id == f["client"].id)):
        bank.verification_status = "DISABLED"
    cancellation = CancellationAgreement(
        milestone_id=f["ms1"].id, requested_by=f["client"].id, basis="MUTUAL", reason="Both parties agree",
        freelancer_gross=1000000, refund_amount=500000, terms_hash="b" * 64, status="ACCEPTED",
        policy_snapshot={}, client_accepted_at=now(), freelancer_accepted_at=now(),
    )
    db.add(cancellation)
    db.commit()
    ref = run_command(db, lambda: DatabaseFinancePort().prepare_cancellation_settlement_in_tx(db, ctx=ctx(f["client"].id), cancellation_id=cancellation.id))
    settlement = db.get(Settlement, ref.settlement_id)
    legs = db.scalars(select(MoneyTransfer).where(MoneyTransfer.settlement_id == settlement.id)).all()
    release = next(row for row in legs if row.purpose == "RELEASE")
    refund = next(row for row in legs if row.purpose == "REFUND")
    assert release.status == "READY" and refund.status == "WAITING_BANK"
    run_command(db, lambda: confirm_transfer_in_tx(db, transfer_id=release.id, payout=payout_data(release)))
    assert settlement.status == "PARTIALLY_SUCCEEDED"
    run_command(db, lambda: banks.add_in_tx(db, user_id=f["client"].id, bank_bin="970422", account_number="666660001", account_name="CLIENT NAME"))
    db.refresh(release)
    db.refresh(refund)
    assert release.status == "SUCCEEDED" and refund.status == "READY"
    run_command(db, lambda: confirm_transfer_in_tx(db, transfer_id=refund.id, payout=payout_data(refund)))
    db.refresh(settlement)
    assert settlement.status == "SUCCEEDED"
    assert db.query(EscrowAccount).one().reserved_amount == 0
    assert_balanced(db)
