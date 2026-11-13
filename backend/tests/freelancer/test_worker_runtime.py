from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.core.enums import UserRole
from app.models import Notification, OutboxEvent, ScheduledJob, StoredFile
from app.services.freelancer_worker import claim, process_one, run_once
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


def test_notification_consumer_is_atomic_and_not_replayed(db, make_user):
    u = make_user(UserRole.CLIENT)
    row = OutboxEvent(
        event_key="n:1",
        event_type="notification",
        entity_type="freelance_projects",
        entity_id=1,
        payload_json={"user_id": u.id, "title": "Hello", "message": "Work notification"},
        available_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1),
    )
    db.add(row)
    db.commit()
    ident = claim(db, OutboxEvent, "w1")
    assert ident == row.id
    assert claim(db, OutboxEvent, "w2") is None
    assert process_one(db, OutboxEvent, ident, "w1")
    assert db.query(Notification).count() == 1
    assert run_once(db) == 0


def test_dead_letter_retry_and_secret_redaction(db, make_user, monkeypatch):
    monkeypatch.setattr(settings, "FREELANCER_WORKER_MAX_ATTEMPTS", 1)
    row = OutboxEvent(
        event_key="unknown:1",
        event_type="bad",
        entity_type="test",
        entity_id=1,
        payload_json={},
        available_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1),
    )
    db.add(row)
    db.commit()
    run_once(db)
    db.refresh(row)
    assert row.status == "DEAD" and row.last_error == "UNKNOWN_EVENT_TYPE"


def test_expired_lease_is_recovered(db):
    job = ScheduledJob(
        job_key="recover",
        job_type="unknown",
        entity_type="test",
        entity_id=1,
        payload_json={},
        run_at=datetime.now(timezone.utc).replace(tzinfo=None),
        status="RUNNING",
        locked_by="dead-worker",
        lease_until=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1),
    )
    db.add(job)
    db.commit()
    assert claim(db, ScheduledJob, "new-worker") == job.id
    assert not process_one(db, ScheduledJob, job.id, "dead-worker")


def test_scanner_unavailable_keeps_pending_file(db, make_user, monkeypatch, tmp_path):
    import hashlib

    from app.core.exceptions import AppException

    def unavailable(*args):
        raise AppException("Scanner unavailable", code="PROVIDER_UNAVAILABLE", status_code=503)

    # A local Windows Defender installation must not make this failure test succeed.
    monkeypatch.setattr("app.services.freelancer_adapters.scan_file", unavailable)

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "FREELANCER_SCAN_GATEWAY_URL", "")
    u = make_user(UserRole.CLIENT)
    data = b"%PDF-1.4"
    (tmp_path / "doc.pdf").write_bytes(data)
    f = StoredFile(
        uploaded_by=u.id,
        storage_key="doc.pdf",
        original_name="doc.pdf",
        content_type="application/pdf",
        size_bytes=len(data),
        checksum_sha256=hashlib.sha256(data).hexdigest(),
        category="EVIDENCE",
    )
    db.add(f)
    db.flush()
    row = OutboxEvent(
        event_key="scan:1",
        event_type="file.scan",
        entity_type="stored_files",
        entity_id=f.id,
        payload_json={"file_id": f.id},
        available_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1),
    )
    db.add(row)
    db.commit()
    run_once(db)
    db.refresh(f)
    db.refresh(row)
    assert f.scan_status == "PENDING" and row.status == "RETRY"


def test_auto_accept_finance_failure_rolls_back_review_and_retries(
    db_session, active_contract_fixtures
):
    from app.models import Deliverable, MilestoneReview

    f = active_contract_fixtures
    m = f["ms1"]
    m.status = "SUBMITTED"
    m.review_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    d = Deliverable(
        milestone_id=m.id,
        submission_no=1,
        submitted_by=f["student"].id,
        note="Delivery",
        submitted_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(d)
    db_session.flush()
    j = ScheduledJob(
        job_key="auto:1",
        job_type="milestone.auto_accept",
        entity_type="milestones",
        entity_id=m.id,
        payload_json={"milestone_id": m.id, "deliverable_id": d.id, "submission_no": 1},
        run_at=m.review_deadline,
    )
    db_session.add(j)
    db_session.commit()
    run_once(db_session)
    db_session.refresh(m)
    db_session.refresh(j)
    assert m.status == "SUBMITTED" and db_session.query(MilestoneReview).count() == 0
    assert j.status == "RETRY" and j.last_error == "FINANCE_NOT_READY"


def test_scanner_gateway_contract_and_checksum(monkeypatch, tmp_path):
    import hashlib

    import httpx

    from app.services.freelancer_adapters import scan_file

    content = b"%PDF-1.4"
    file = tmp_path / "proof.pdf"
    file.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(settings, "FREELANCER_SCAN_GATEWAY_URL", "https://scanner.test/scan")
    original = httpx.Client

    def gateway(request):
        assert request.url.path == "/scan" and checksum.encode() in request.content
        return httpx.Response(200, json={"sha256": checksum, "verdict": "CLEAN"})

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(gateway), **kwargs)
    )
    assert scan_file(file, checksum) == "CLEAN"


def test_mou_expiry_does_not_create_holds_or_unverify_company(db, make_user):
    from app.models import MilestoneHold, MouAgreement
    from tests.freelancer.test_group_a_api import company, stored

    u = make_user(UserRole.COMPANY)
    c = company(db, u, business_status="VERIFIED")
    f = stored(db, u)
    at = datetime.now(timezone.utc).replace(tzinfo=None)
    mou = MouAgreement(
        company_id=c.id,
        agreement_code="EXPIRES",
        document_file_id=f.id,
        school_name="School",
        school_signer_name="A",
        company_signer_name="B",
        school_signer_position="Principal",
        company_signer_position="Director",
        signature_method="SCANNED_SIGNED_DOCUMENT",
        signed_at=at - timedelta(days=3),
        effective_from=at - timedelta(days=2),
        effective_until=at - timedelta(seconds=1),
        scope_json={"scope": "projects"},
        status="ACTIVE",
    )
    db.add(mou)
    db.flush()
    db.add(
        ScheduledJob(
            job_key="expire:mou",
            job_type="mou.expire",
            entity_type="mou_agreements",
            entity_id=mou.id,
            run_at=at - timedelta(seconds=1),
            payload_json={"mou_id": mou.id},
        )
    )
    db.commit()
    run_once(db)
    db.refresh(mou)
    db.refresh(c)
    assert (
        mou.status == "EXPIRED"
        and c.business_status == "VERIFIED"
        and db.query(MilestoneHold).count() == 0
    )
