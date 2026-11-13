"""Domain workflow tests with explicit finance doubles; not financial-writer tests."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.enums import UserRole, UserStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models import (
    ActiveMilestoneDispute,
    Dispute,
    DisputeDecision,
    EscrowAccount,
    LedgerAccount,
    MilestoneHold,
    User,
)
from app.schemas.freelancer_disputes import (
    CancellationCreate,
    DecisionCreate,
    DisputeCreate,
    EvidenceCreate,
)
from app.services import cancellation_service as cs
from app.services import dispute_service as ds
from app.services.freelancer_commands import run_command
from app.services.freelancer_finance import FinanceNotReadyError
from tests.freelancer.fakes import FakeFinancePort
from tests.freelancer.test_group_c_milestones_deliverables import (
    active_contract_fixtures as _active_fixture,
)
from tests.freelancer.test_group_c_milestones_deliverables import (
    db_session as _session_fixture,
)


@pytest.fixture
def db_session():
    yield from _session_fixture.__wrapped__()


@pytest.fixture
def active_contract_fixtures(db_session):
    return _active_fixture.__wrapped__(db_session)


@pytest.fixture
def domain(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    db = db_session
    admin = User(
        id=901, email="admin901@test.invalid", role=UserRole.ADMIN, status=UserStatus.ACTIVE
    )
    admin2 = User(
        id=902, email="admin902@test.invalid", role=UserRole.ADMIN, status=UserStatus.ACTIVE
    )
    db.add_all([admin, admin2])
    db.flush()
    account = LedgerAccount(
        code="TEST:ESCROW", kind="ESCROW_HELD", normal_side="C", milestone_id=f["ms1"].id
    )
    db.add(account)
    db.flush()
    escrow = EscrowAccount(
        milestone_id=f["ms1"].id, ledger_account_id=account.id, funded_amount=1500000
    )
    db.add(escrow)
    f["ms1"].status = "SUBMITTED"
    f["ms1"].review_deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5)
    db.commit()
    return {**f, "admin": admin, "admin2": admin2, "escrow": escrow}


def open_d(db, f, finance=None):
    return run_command(
        db,
        lambda: ds.open_in_tx(
            db,
            user_id=f["client"].id,
            milestone_id=f["ms1"].id,
            payload=DisputeCreate(reason_code="QUALITY", description="Does not meet criteria"),
            finance=finance or FakeFinancePort(funded=True),
        ),
    )


def test_open_dispute_records_guard_hold_and_pauses_review(db_session, domain):
    f = domain
    data = open_d(db_session, f)
    d = db_session.get(Dispute, int(data["id"]))
    assert d.remaining_review_seconds > 0 and d.previous_milestone_status == "SUBMITTED"
    assert f["ms1"].status == "DISPUTED" and f["ms1"].review_deadline is None
    assert db_session.get(ActiveMilestoneDispute, f["ms1"].id).dispute_id == d.id
    assert db_session.query(MilestoneHold).filter_by(dispute_id=d.id).count() == 1
    with pytest.raises(ConflictError):
        open_d(db_session, f)


def test_funded_not_started_milestone_can_open_admin_dispute(db_session, domain):
    f = domain
    f["ms1"].status = "FUNDED"
    f["ms1"].started_at = None
    f["ms1"].review_deadline = None
    db_session.commit()

    data = run_command(
        db_session,
        lambda: ds.open_in_tx(
            db_session,
            user_id=f["client"].id,
            milestone_id=f["ms1"].id,
            payload=DisputeCreate(
                reason_code="NON_COOPERATION",
                description="The student did not respond to the mutual cancellation request",
            ),
            finance=FakeFinancePort(funded=True),
        ),
    )

    dispute = db_session.get(Dispute, int(data["id"]))
    assert dispute.previous_milestone_status == "FUNDED"
    assert f["ms1"].status == "DISPUTED"


def test_finance_unavailable_rolls_back_opening(db_session, domain):
    f = domain
    with pytest.raises(FinanceNotReadyError):
        run_command(
            db_session,
            lambda: ds.open_in_tx(
                db_session,
                user_id=f["client"].id,
                milestone_id=f["ms1"].id,
                payload=DisputeCreate(reason_code="QUALITY", description="Work issue"),
            ),
        )
    assert db_session.query(Dispute).count() == 0 and db_session.query(MilestoneHold).count() == 0
    assert f["ms1"].status == "SUBMITTED"


def test_dispute_evidence_private_and_deadline_enforced(db_session, domain):
    f = domain
    did = int(open_d(db_session, f)["id"])
    with pytest.raises(NotFoundError):
        ds.get_dispute(db_session, user_id=f["outsider"].id, dispute_id=did)
    db_session.rollback()
    with pytest.raises(BadRequestError):
        run_command(
            db_session,
            lambda: ds.evidence_in_tx(
                db_session, user_id=f["client"].id, dispute_id=did, payload=EvidenceCreate()
            ),
        )
    result = run_command(
        db_session,
        lambda: ds.evidence_in_tx(
            db_session,
            user_id=f["student"].id,
            dispute_id=did,
            payload=EvidenceCreate(note="My delivery notes"),
        ),
    )
    assert result["note"] == "My delivery notes"
    d = db_session.get(Dispute, did)
    d.evidence_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()
    with pytest.raises(ConflictError):
        run_command(
            db_session,
            lambda: ds.evidence_in_tx(
                db_session,
                user_id=f["student"].id,
                dispute_id=did,
                payload=EvidenceCreate(note="Late"),
            ),
        )


def test_withdrawal_requires_other_party_and_preserves_other_holds(db_session, domain):
    f = domain
    did = int(open_d(db_session, f)["id"])
    db_session.add(
        MilestoneHold(
            milestone_id=f["ms1"].id,
            reason_type="ADMIN_REVIEW",
            reason_key="test-admin",
            placed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            note="Independent review",
        )
    )
    db_session.commit()
    w = run_command(
        db_session,
        lambda: ds.request_withdrawal_in_tx(
            db_session, user_id=f["client"].id, dispute_id=did, reason="Agreed to continue"
        ),
    )
    with pytest.raises(ForbiddenError):
        run_command(
            db_session,
            lambda: ds.confirm_withdrawal_in_tx(
                db_session, user_id=f["client"].id, dispute_id=did, content_hash=w["terms_hash"]
            ),
        )
    result = run_command(
        db_session,
        lambda: ds.confirm_withdrawal_in_tx(
            db_session, user_id=f["student"].id, dispute_id=did, content_hash=w["terms_hash"]
        ),
    )
    assert result["status"] == "WITHDRAWN" and f["ms1"].status == "SUBMITTED"
    assert f["ms1"].review_deadline > datetime.now(timezone.utc).replace(tzinfo=None)
    assert (
        db_session.query(MilestoneHold).filter_by(reason_key="test-admin").one().released_at is None
    )
    assert db_session.query(MilestoneHold).filter_by(dispute_id=did).one().released_at is not None


def proposal(db, f, did):
    d = db.get(Dispute, did)
    d.evidence_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    db.commit()
    return run_command(
        db,
        lambda: ds.decision_in_tx(
            db,
            user_id=f["admin"].id,
            dispute_id=did,
            payload=DecisionCreate(
                outcome="SPLIT",
                freelancer_gross=1000000,
                refund_amount=500000,
                reason="Partial completion",
            ),
        ),
    )


def test_single_admin_split_decision_is_immediately_approved(db_session, domain):
    f = domain
    did = int(open_d(db_session, f)["id"])
    decision = proposal(db_session, f, did)
    decision_id = int(decision["id"])
    assert not decision["requires_second_approval"]
    assert decision["status"] == "APPROVED"
    with pytest.raises(ConflictError, match="closed evidence collection"):
        run_command(
            db_session,
            lambda: ds.evidence_in_tx(
                db_session,
                user_id=f["student"].id,
                dispute_id=did,
                payload=EvidenceCreate(note="Late evidence after final decision"),
            ),
        )
    with pytest.raises(ConflictError):
        proposal(db_session, f, did)
    with pytest.raises(FinanceNotReadyError):
        run_command(
            db_session,
            lambda: ds.execute_decision_in_tx(
                db_session, user_id=f["admin"].id, decision_id=decision_id
            ),
        )
    assert db_session.get(DisputeDecision, decision_id).status == "APPROVED"
    run_command(
        db_session,
        lambda: ds.execute_decision_in_tx(
            db_session,
            user_id=f["admin"].id,
            decision_id=decision_id,
            finance=FakeFinancePort(funded=True),
        ),
    )
    assert db_session.get(DisputeDecision, decision_id).status == "EXECUTING"
    assert db_session.get(Dispute, did).status != "RESOLVED"
    assert db_session.get(ActiveMilestoneDispute, f["ms1"].id)


def test_other_hold_blocks_decision_without_mutating_it(db_session, domain):
    f = domain
    did = int(open_d(db_session, f)["id"])
    decision_id = int(proposal(db_session, f, did)["id"])
    db_session.add(
        MilestoneHold(
            milestone_id=f["ms1"].id,
            reason_type="COMPANY_SUSPENSION",
            reason_key="suspension",
            placed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            note="Suspended",
        )
    )
    db_session.commit()
    with pytest.raises(ConflictError):
        run_command(
            db_session,
            lambda: ds.execute_decision_in_tx(
                db_session,
                user_id=f["admin2"].id,
                decision_id=decision_id,
                finance=FakeFinancePort(funded=True),
            ),
        )
    assert db_session.get(DisputeDecision, decision_id).status == "APPROVED"


def test_unfunded_cancellation_mutual_executes_without_zero_transfer(db_session, domain):
    f = domain
    mid = f["ms2"].id
    result = run_command(
        db_session,
        lambda: cs.create_in_tx(
            db_session,
            user_id=f["client"].id,
            milestone_id=mid,
            payload=CancellationCreate(
                basis="MUTUAL", reason="Scope removed", freelancer_gross=0, refund_amount=0
            ),
        ),
    )
    cid = int(result["id"])
    run_command(
        db_session,
        lambda: cs.action_in_tx(
            db_session,
            user_id=f["student"].id,
            cancellation_id=cid,
            action="accept",
            content_hash=result["terms_hash"],
        ),
    )
    result = run_command(
        db_session,
        lambda: cs.execute_in_tx(db_session, user_id=f["client"].id, cancellation_id=cid),
    )
    assert result["status"] == "EXECUTED" and f["ms2"].status == "CANCELLED"


def test_unilateral_cancellation_requires_signed_clause(db_session, domain):
    f = domain
    with pytest.raises(ConflictError):
        run_command(
            db_session,
            lambda: cs.create_in_tx(
                db_session,
                user_id=f["client"].id,
                milestone_id=f["ms2"].id,
                payload=CancellationCreate(
                    basis="BEFORE_START", reason="Cancel", freelancer_gross=0, refund_amount=0
                ),
            ),
        )


def test_funded_milestone_never_allows_unilateral_cancellation(db_session, domain):
    f = domain
    f["ms1"].status = "FUNDED"
    f["ms1"].started_at = None
    db_session.commit()

    with pytest.raises(ConflictError, match="mutual cancellation or an administrator dispute"):
        run_command(
            db_session,
            lambda: cs.create_in_tx(
                db_session,
                user_id=f["client"].id,
                milestone_id=f["ms1"].id,
                payload=CancellationCreate(
                    basis="BEFORE_START",
                    reason="Cancel after funding",
                    freelancer_gross=0,
                    refund_amount=f["escrow"].funded_amount,
                ),
            ),
        )


def test_dispute_api_permission_idempotency_and_unavailable_finance(
    db_session, domain, monkeypatch
):
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.core.security import create_access_token
    from app.main import create_app

    f = domain
    app = create_app()

    def session():
        yield db_session

    app.dependency_overrides[get_db] = session

    def headers(u, key="open-test"):
        return {
            "Authorization": "Bearer " + create_access_token(u.id, u.role.value),
            "Idempotency-Key": key,
        }

    url = f"/api/v1/milestones/{f['ms1'].id}/disputes"
    body = {"reason_code": "QUALITY", "description": "Incomplete work"}
    with TestClient(app) as client:
        assert client.post(url, headers=headers(f["outsider"]), json=body).status_code == 404
        r = client.post(url, headers=headers(f["client"]), json=body)
        assert r.status_code == 503, r.text
        assert db_session.query(Dispute).count() == 0
        monkeypatch.setattr(ds, "get_finance_port", lambda: FakeFinancePort(funded=True))
        r = client.post(url, headers=headers(f["client"]), json=body)
        assert r.status_code == 201, r.text
        assert client.post(url, headers=headers(f["client"]), json=body).json() == r.json()
        assert (
            client.post(
                url, headers=headers(f["client"]), json={**body, "description": "Another request"}
            ).status_code
            == 409
        )
        did = r.json()["data"]["id"]
        assert (
            client.get(f"/api/v1/disputes/{did}", headers=headers(f["outsider"])).status_code == 404
        )
        assert (
            client.get(f"/api/v1/admin/disputes/{did}", headers=headers(f["student"])).status_code
            == 403
        )
        assert (
            client.get(f"/api/v1/admin/disputes/{did}", headers=headers(f["admin"])).status_code
            == 200
        )


def test_company_resume_does_not_remove_dispute_hold(db_session, domain):
    from app.models import Company, FreelanceProject
    from app.services.business_verification_service import suspension_in_tx

    f = domain
    company = Company(
        user_id=f["client"].id, name="Business", tax_code="0987654321", business_status="VERIFIED"
    )
    db_session.add(company)
    db_session.flush()
    f["client"].role = UserRole.COMPANY
    p = db_session.get(FreelanceProject, f["contract"].project_id)
    p.company_id = company.id
    f["contract"].company_id = company.id
    db_session.commit()
    did = int(open_d(db_session, f)["id"])
    run_command(
        db_session,
        lambda: suspension_in_tx(
            db_session,
            user_id=f["admin"].id,
            company_id=company.id,
            suspend=True,
            reason="Compliance review",
        ),
    )
    assert (
        db_session.query(MilestoneHold)
        .filter_by(reason_type="COMPANY_SUSPENSION", released_at=None)
        .count()
        > 0
    )
    run_command(
        db_session,
        lambda: suspension_in_tx(
            db_session,
            user_id=f["admin"].id,
            company_id=company.id,
            suspend=False,
            reason="Review completed",
        ),
    )
    assert (
        db_session.query(MilestoneHold)
        .filter_by(reason_type="COMPANY_SUSPENSION", released_at=None)
        .count()
        == 0
    )
    assert db_session.query(MilestoneHold).filter_by(dispute_id=did, released_at=None).count() == 1
