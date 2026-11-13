"""Frontend read models must preserve party and administrator boundaries."""

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.enums import UserRole, UserStatus
from app.core.security import create_access_token
from app.main import app
from app.models import Dispute, DisputeDecision, FreelanceProject, PaymentOrder, User
from app.services.freelancer_domain import now
from tests.freelancer.test_group_c_milestones_deliverables import (
    active_contract_fixtures as _active,
)
from tests.freelancer.test_group_c_milestones_deliverables import db_session as _session


@pytest.fixture
def db_session():
    yield from _session.__wrapped__()


@pytest.fixture
def workspace(db_session):
    from app.models import FinanceCounter
    f = _active.__wrapped__(db_session)
    db_session.add_all(
        [
            FinanceCounter(name="writer", next_value=1000000000),
            User(
                id=901,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                email="workspace-admin@test.invalid",
            ),
            User(
                id=4,
                role=UserRole.CLIENT,
                status=UserStatus.ACTIVE,
                email="other-client@test.invalid",
            ),
        ]
    )
    db_session.commit()
    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client, db_session, f
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


def auth(uid, role):
    return {"Authorization": "Bearer " + create_access_token(uid, role)}


def test_bank_inspection_is_admin_only_audited_and_not_cacheable(workspace, monkeypatch):
    from cryptography.fernet import Fernet

    from app.core.config import settings
    from app.models import AuditLog
    from app.services import freelancer_bank_service as banks
    from app.services.freelancer_commands import run_command

    client, db, _ = workspace
    monkeypatch.setattr(settings, "FREELANCER_BANK_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr(
        settings, "FREELANCER_BANK_FINGERPRINT_KEY", "test-bank-fingerprint-separate-key-12345"
    )
    result = run_command(
        db,
        lambda: banks.add_in_tx(
            db,
            user_id=2,
            bank_bin="970422",
            account_number="123456789012",
            account_name="STUDENT TEST",
        ),
    )
    url = f"/api/v1/admin/bank-destinations/{result['id']}/verification-data"
    body = {"reason": "Checking account ownership evidence"}
    assert client.post(url, json=body, headers=auth(2, "STUDENT")).status_code == 403
    response = client.post(url, json=body, headers=auth(901, "ADMIN"))
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert response.json()["data"]["account_number"] == "123456789012"
    assert "ciphertext" not in response.text
    log = db.query(AuditLog).filter_by(action="bank_destination.inspected").one()
    assert log.actor_user_id == 901 and log.after_json is None and "123456789012" not in log.reason
    assert (
        "123456789012"
        not in client.get("/api/v1/bank-destinations", headers=auth(2, "STUDENT")).text
    )


def test_project_review_feedback_is_private_and_available_for_revision(workspace):
    client, db, f = workspace
    p = db.get(FreelanceProject, f["contract"].project_id)
    p.status = "NEEDS_REVISION"
    p.review_reason = "Clarify deliverables before approval"
    db.commit()
    url = f"/api/v1/freelance-projects/{p.id}"
    assert (
        client.get(url, headers=auth(1, "CLIENT")).json()["data"]["review_reason"]
        == p.review_reason
    )
    assert client.get(url, headers=auth(3, "STUDENT")).status_code == 404
    p.status = "APPROVED"
    db.commit()
    assert "review_reason" not in client.get(url, headers=auth(3, "STUDENT")).json()["data"]


@pytest.mark.parametrize(
    "uid,role,count",
    [(1, "CLIENT", 1), (2, "STUDENT", 1), (3, "STUDENT", 0), (4, "CLIENT", 0), (901, "ADMIN", 1)],
)
def test_contract_index_scopes_each_viewer(workspace, uid, role, count):
    client, _, _ = workspace
    result = client.get("/api/v1/freelancer/contracts", headers=auth(uid, role))
    assert result.status_code == 200
    assert len(result.json()["items"]) == count


def test_overview_aggregates_only_the_current_users_contracts(workspace):
    client, _, _ = workspace
    own = client.get("/api/v1/freelancer/overview", headers=auth(1, "CLIENT"))
    assert own.status_code == 200
    assert own.json()["data"]["active_contracts"] == 1
    other = client.get("/api/v1/freelancer/overview", headers=auth(4, "CLIENT")).json()["data"]
    assert other["active_contracts"] == 0 and other["funded_amount"] == "0"
    assert "pending_verifications" not in other
    assert (
        "pending_verifications"
        in client.get("/api/v1/freelancer/overview", headers=auth(901, "ADMIN")).json()["data"]
    )


def test_activity_hides_other_parties_and_draft_decisions(workspace):
    client, db, f = workspace
    d = Dispute(
        milestone_id=f["ms1"].id,
        opened_by=1,
        reason_code="QUALITY",
        description="Review requested",
        previous_milestone_status="SUBMITTED",
        evidence_deadline=now(),
    )
    db.add(d)
    db.flush()
    for revision, status in ((1, "PROPOSED"), (2, "APPROVED")):
        db.add(
            DisputeDecision(
                dispute_id=d.id,
                revision_no=revision,
                outcome="PAYOUT",
                freelancer_gross=1500000,
                refund_amount=0,
                reason="Decision evidence",
                status=status,
                requires_second_approval=False,
                approval_threshold_snapshot=5000000,
                proposed_by=901,
            )
        )
    db.commit()
    url = f"/api/v1/milestones/{f['ms1'].id}/activity"
    assert client.get(url, headers=auth(3, "STUDENT")).status_code == 404
    party = client.get(url, headers=auth(2, "STUDENT")).json()["data"]["disputes"][0]
    assert [row["status"] for row in party["decisions"]] == ["APPROVED"]
    admin = client.get(url, headers=auth(901, "ADMIN")).json()["data"]["disputes"][0]
    assert len(admin["decisions"]) == 2


def test_evidence_includes_sender_identity_and_role(workspace):
    from app.models import DisputeEvidence, Student

    client, db, f = workspace
    dispute = Dispute(
        milestone_id=f["ms1"].id, opened_by=1, reason_code="QUALITY",
        description="Review", previous_milestone_status="SUBMITTED", evidence_deadline=now(),
    )
    db.add(dispute)
    db.flush()
    db.add_all([
        DisputeEvidence(dispute_id=dispute.id, submitted_by=2, note="Student evidence"),
        DisputeEvidence(dispute_id=dispute.id, submitted_by=1, note="Client evidence"),
    ])
    db.commit()
    result = client.get(f"/api/v1/disputes/{dispute.id}/evidence", headers=auth(2, "STUDENT"))
    assert result.status_code == 200, result.text
    items = result.json()["items"]
    assert items[0]["submitted_by_name"] == db.get(Student, f["contract"].freelancer_student_id).full_name
    assert items[0]["submitted_by_role_label"] == "Sinh viên"
    assert items[1]["submitted_by_role_label"] == "Người thuê"
    assert "@" in items[1]["submitted_by_name"]


def test_payment_return_lookup_does_not_grant_access_by_order_code(workspace):
    client, db, f = workspace
    db.add(
        PaymentOrder(
            milestone_id=f["ms1"].id,
            payer_user_id=1,
            expected_amount=1500000,
            order_code=1000000001,
            request_key="return-test",
            request_hash="a" * 64,
            receiving_account_snapshot={},
            expires_at=now(),
        )
    )
    db.commit()
    url = "/api/v1/payment-orders/by-code/1000000001"
    assert client.get(url, headers=auth(3, "STUDENT")).status_code == 404
    assert client.get(url, headers=auth(1, "CLIENT")).json()["data"]["status"] == "CREATING"


@pytest.mark.parametrize(
    "url", ["/admin/mou-agreements", "/admin/freelance-expansions", "/admin/finance/journals"]
)
def test_staff_read_models_are_admin_only(workspace, url):
    client, _, _ = workspace
    assert client.get("/api/v1" + url, headers=auth(2, "STUDENT")).status_code == 403
    assert client.get("/api/v1" + url, headers=auth(901, "ADMIN")).status_code == 200
