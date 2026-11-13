"""Regression tests against the real app registry and real persisted models."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.core.enums import UserRole, UserStatus
from app.models import Company, MouAgreement, StoredFile, UserVerification
from app.services.freelancer_accounts import otp_service

BASE = "/api/v1"


@pytest.fixture
def otp(monkeypatch):
    sent = []
    monkeypatch.setattr(settings, "FREELANCER_OTP_SECRET", "x" * 40)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(
        otp_service, "deliver_code", lambda channel, target, code: sent.append((target, code))
    )
    return sent


def test_routes_exist_on_actual_app(client):
    paths = client.get(BASE + "/openapi.json").json()["paths"]
    assert BASE + "/client-accounts/otp/verify" in paths
    assert BASE + "/company/verification/submit-legal-docs" in paths
    assert BASE + "/mou-agreements/" in paths
    assert BASE + "/files/{file_id}/download" in paths


def test_otp_persists_attempts_consumes_once_and_verifies_email(
    client, db, make_user, auth_headers, otp
):
    u = make_user(UserRole.CLIENT)
    h = auth_headers(u)
    data = {"identifier": u.email}
    response = client.post(BASE + "/client-accounts/otp/request", headers=h, json=data)
    assert response.status_code == 200
    code = otp[0][1]
    assert code not in response.text
    record = db.query(UserVerification).one()
    assert record.otp_hash != code and record.status == "PENDING"
    wrong = "000000" if code != "000000" else "111111"
    assert (
        client.post(
            BASE + "/client-accounts/otp/verify", headers=h, json={**data, "code": wrong}
        ).status_code
        == 409
    )
    db.refresh(record)
    assert record.attempts == 1
    assert (
        client.post(
            BASE + "/client-accounts/otp/verify", headers=h, json={**data, "code": code}
        ).status_code
        == 200
    )
    db.refresh(u)
    assert u.email_verified_at is not None
    assert (
        client.post(
            BASE + "/client-accounts/otp/verify", headers=h, json={**data, "code": code}
        ).status_code
        == 409
    )


def test_otp_without_challenge_fails(client, make_user, auth_headers, otp):
    u = make_user(UserRole.CLIENT)
    assert (
        client.post(
            BASE + "/client-accounts/otp/verify",
            headers=auth_headers(u),
            json={"identifier": u.email, "code": "000000"},
        ).status_code
        == 409
    )


def test_contact_status_is_persisted_scoped_and_resumes_challenge(
    client, db, make_user, auth_headers, otp
):
    first = make_user(UserRole.CLIENT)
    second = make_user(UserRole.CLIENT)
    headers = auth_headers(first)
    path = BASE + "/auth/verification-status"
    assert client.get(path).status_code == 401
    before = client.get(path, headers=headers).json()["data"]["contacts"]
    assert before["EMAIL"]["identifier"] == first.email
    assert before["EMAIL"]["verified"] is False
    sent = client.post(
        BASE + "/auth/verifications", headers=headers, json={"identifier": first.email}
    )
    assert sent.status_code == 200
    payload = sent.json()["data"]
    assert payload["expires_at"] and payload["resend_after"] and payload["server_time"]
    current = client.get(path, headers=headers)
    challenge = current.json()["data"]["contacts"]["EMAIL"]["challenge"]
    assert challenge["challenge_id"] == payload["challenge_id"]
    assert challenge["attempts_left"] == 5
    assert "otp_hash" not in current.text and "key_version" not in current.text
    assert otp[0][1] not in current.text
    assert (
        client.get(path, headers=auth_headers(second)).json()["data"]["contacts"]["EMAIL"][
            "challenge"
        ]
        is None
    )
    code = otp[0][1]
    verify = BASE + "/auth/verifications/" + payload["challenge_id"] + "/verify"
    wrong = "000000" if code != "000000" else "111111"
    assert (
        client.post(
            verify, headers=headers, json={"identifier": first.email, "code": wrong}
        ).status_code
        == 409
    )
    assert (
        client.get(path, headers=headers).json()["data"]["contacts"]["EMAIL"]["challenge"][
            "attempts_left"
        ]
        == 4
    )
    assert (
        client.post(
            verify, headers=headers, json={"identifier": first.email, "code": code}
        ).status_code
        == 200
    )
    final = client.get(path, headers=headers).json()["data"]["contacts"]
    assert final["EMAIL"]["verified"] is True and final["EMAIL"]["verified_at"]
    assert final["EMAIL"]["challenge"] is None
    assert "PHONE" not in final


def test_pending_company_can_read_own_verification_status(client, make_user, auth_headers):
    company = make_user(UserRole.COMPANY, status=UserStatus.PENDING_APPROVAL)
    response = client.get(BASE + "/auth/verification-status", headers=auth_headers(company))
    assert response.status_code == 200
    assert response.json()["data"]["contacts"]["EMAIL"]["identifier"] == company.email


def test_profile_read_returns_only_current_clients_profile(client, db, make_user, auth_headers):
    from app.models import ClientProfile

    first = make_user(UserRole.CLIENT)
    second = make_user(UserRole.CLIENT)
    admin = make_user(UserRole.ADMIN)
    db.add_all(
        [
            ClientProfile(user_id=first.id, full_name="First"),
            ClientProfile(user_id=second.id, full_name="Second"),
        ]
    )
    db.commit()
    path = BASE + "/client-accounts/me"
    assert client.get(path, headers=auth_headers(first)).json()["data"]["full_name"] == "First"
    assert client.get(path, headers=auth_headers(second)).json()["data"]["full_name"] == "Second"
    assert client.get(path, headers=auth_headers(admin)).status_code == 403


def test_otp_send_rate_limit_is_persistent(client, make_user, auth_headers, otp):
    u = make_user(UserRole.CLIENT)
    for expected in (200, 429):
        assert (
            client.post(
                BASE + "/client-accounts/otp/request",
                headers=auth_headers(u),
                json={"identifier": u.email},
            ).status_code
            == expected
        )
    assert len(otp) == 1


def test_otp_wrong_target_and_unconfigured_transport(
    client, make_user, auth_headers, otp, monkeypatch
):
    u = make_user(UserRole.CLIENT)
    assert (
        client.post(
            BASE + "/client-accounts/otp/request",
            headers=auth_headers(u),
            json={"identifier": "victim@test.com"},
        ).status_code
        == 403
    )
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    assert (
        client.post(
            BASE + "/client-accounts/otp/request",
            headers=auth_headers(u),
            json={"identifier": u.email},
        ).status_code
        == 503
    )


def test_otp_attempt_limit_and_expiry(client, db, make_user, auth_headers, otp):
    u = make_user(UserRole.CLIENT)
    h, data = auth_headers(u), {"identifier": u.email}
    client.post(BASE + "/client-accounts/otp/request", headers=h, json=data)
    code = otp[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert (
            client.post(
                BASE + "/client-accounts/otp/verify", headers=h, json={**data, "code": wrong}
            ).status_code
            == 409
        )
    assert (
        client.post(
            BASE + "/client-accounts/otp/verify", headers=h, json={**data, "code": code}
        ).status_code
        == 409
    )
    record = db.query(UserVerification).one()
    assert record.attempts == 5 and record.status == "LOCKED"


def test_delivery_failure_invalidates_challenge(
    client, db, make_user, auth_headers, otp, monkeypatch
):
    def fail(*args):
        raise RuntimeError("transport failure")

    monkeypatch.setattr(otp_service, "deliver_code", fail)
    u = make_user(UserRole.CLIENT)
    r = client.post(
        BASE + "/client-accounts/otp/request", headers=auth_headers(u), json={"identifier": u.email}
    )
    assert r.status_code == 503
    assert db.query(UserVerification).one().status == "SUPERSEDED"


def stored(db, u, **kw):
    fields = dict(
        uploaded_by=u.id,
        storage_key=f"docs/{u.id}.pdf",
        original_name="proof.pdf",
        content_type="application/pdf",
        size_bytes=10,
        checksum_sha256="a" * 64,
        category="BUSINESS_LICENSE",
        scan_status="CLEAN",
        availability_status="AVAILABLE",
    )
    fields.update(kw)
    f = StoredFile(**fields)
    db.add(f)
    db.commit()
    return f


def company(db, u, **kw):
    u.email_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    c = Company(user_id=u.id, name="Example", tax_code="0123456789", **kw)
    db.add(c)
    db.commit()
    return c


def test_retired_business_submission_is_removed(client):
    assert client.post(BASE + "/business-verifications/", json={}).status_code == 404


def mou_payload(c, f):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return dict(
        company_id=str(c.id),
        mou_code="MOU-2026-1",
        document_file_id=str(f.id),
        school_name="School",
        school_signer_name="School signer",
        company_signer_name="Company signer",
        school_signer_position="Principal",
        company_signer_position="Director",
        signed_at=(now - timedelta(days=2)).isoformat(),
        effective_from=(now - timedelta(days=1)).isoformat(),
        effective_until=(now + timedelta(days=365)).isoformat(),
        scope_json={"scope": "student projects"},
    )


def test_mou_persists_required_fields_and_ownership(client, db, make_user, auth_headers):
    u = make_user(UserRole.COMPANY)
    c = company(db, u, business_status="VERIFIED")
    reviewer = make_user(UserRole.ADMIN)
    f = stored(db, reviewer)
    other = make_user(UserRole.CLIENT)
    data = mou_payload(c, f)
    assert (
        client.post(BASE + "/mou-agreements/", headers=auth_headers(other), json=data).status_code
        == 403
    )
    r = client.post(BASE + "/mou-agreements/", headers=auth_headers(reviewer), json=data)
    assert r.status_code == 201, r.text
    m = db.query(MouAgreement).one()
    assert m.agreement_code == data["mou_code"] and m.status == "PENDING_REVIEW"
    assert m.signature_verification_status == "NOT_CHECKED"
    assert (
        client.post(
            BASE + "/mou-agreements/", headers=auth_headers(reviewer), json=data
        ).status_code
        == 409
    )


def test_file_permissions_scan_path_and_real_content(
    client, db, make_user, auth_headers, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    u = make_user(UserRole.CLIENT)
    other = make_user(UserRole.CLIENT)
    f = stored(db, u)
    url = BASE + f"/files/{f.id}/download"
    assert client.get(url, headers=auth_headers(other)).status_code == 404
    assert client.get(url, headers=auth_headers(u)).status_code == 404
    (tmp_path / "docs").mkdir()
    (tmp_path / f.storage_key).write_bytes(b"real file")
    import hashlib
    f.checksum_sha256 = hashlib.sha256(b"real file").hexdigest()
    f.size_bytes = len(b"real file")
    db.commit()
    r = client.get(url, headers=auth_headers(u))
    assert r.status_code == 200 and r.content == b"real file"
    f.scan_status = "PENDING"
    db.commit()
    assert client.get(url, headers=auth_headers(u)).status_code == 409
    f.scan_status = "CLEAN"
    f.storage_key = "../outside.pdf"
    db.commit()
    assert client.get(url, headers=auth_headers(u)).status_code == 404


def test_client_eligibility_matches_approved_policy(client, db, make_user, auth_headers):
    u = make_user(UserRole.CLIENT)
    h = auth_headers(u)
    r = client.get(BASE + "/client-accounts/eligibility/me", headers=h)
    assert r.status_code == 200 and not r.json()["can_draft"]
    u.email_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    r = client.get(BASE + "/client-accounts/eligibility/me", headers=h).json()
    assert r["can_draft"] and r["can_submit"] and r["can_fund"]
    assert u.phone_verified_at is None
    assert "PHONE_NOT_VERIFIED" not in r["reason_codes"]


def test_company_eligibility_valid_mou_not_hidden_by_future_one(
    client, db, make_user, auth_headers
):
    from app.services.freelancer_accounts.eligibility_service import company_has_valid_mou

    u = make_user(UserRole.COMPANY)
    c = company(db, u, business_status="VERIFIED")
    f = stored(db, u)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    data = mou_payload(c, f)
    for num, start in ((1, now - timedelta(days=1)), (2, now + timedelta(days=1))):
        db.add(
            MouAgreement(
                company_id=c.id,
                agreement_code=f"CODE{num}",
                document_file_id=f.id,
                school_name="School",
                school_signer_name="A",
                company_signer_name="B",
                school_signer_position="P",
                company_signer_position="D",
                signature_method="SCANNED_SIGNED_DOCUMENT",
                signed_at=now,
                effective_from=start,
                effective_until=now + timedelta(days=10),
                scope_json=data["scope_json"],
                status="ACTIVE",
            )
        )
    db.commit()
    assert company_has_valid_mou(db, c.id, now)
    assert (
        client.get(BASE + "/client-accounts/eligibility/me", headers=auth_headers(u)).json()["tier"]
        == "OFFICIAL_PARTNER"
    )


def test_expired_otp_and_resend_supersedes_old_challenge(
    client, db, make_user, auth_headers, otp, monkeypatch
):
    u = make_user(UserRole.CLIENT)
    h, data = auth_headers(u), {"identifier": u.email}
    now = datetime(2026, 11, 7, 12)
    monkeypatch.setattr(otp_service, "now_utc", lambda: now)
    assert (
        client.post(BASE + "/client-accounts/otp/request", headers=h, json=data).status_code == 200
    )
    old_code = otp[0][1]
    now += timedelta(minutes=16)
    assert (
        client.post(
            BASE + "/client-accounts/otp/verify", headers=h, json={**data, "code": old_code}
        ).status_code
        == 409
    )
    assert db.query(UserVerification).one().status == "EXPIRED"
    assert (
        client.post(BASE + "/client-accounts/otp/request", headers=h, json=data).status_code == 200
    )
    now += timedelta(minutes=1)
    assert (
        client.post(BASE + "/client-accounts/otp/request", headers=h, json=data).status_code == 200
    )
    rows = db.query(UserVerification).order_by(UserVerification.id).all()
    assert [r.status for r in rows] == ["EXPIRED", "SUPERSEDED", "PENDING"]


def test_removed_sms_and_missing_email_secret_fail_closed(client, make_user, auth_headers, otp, monkeypatch):
    u = make_user(UserRole.CLIENT)
    assert (
        client.post(
            BASE + "/client-accounts/otp/request",
            headers=auth_headers(u),
            json={"identifier": "0900000000", "channel": "PHONE"},
        ).status_code
        == 422
    )
    monkeypatch.setattr(settings, "FREELANCER_OTP_SECRET", "")
    assert (
        client.post(
            BASE + "/client-accounts/otp/request",
            headers=auth_headers(u),
            json={"identifier": u.email},
        ).status_code
        == 503
    )
