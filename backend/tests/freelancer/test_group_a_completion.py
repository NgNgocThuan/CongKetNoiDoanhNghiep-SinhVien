from datetime import datetime

from app.core.config import settings
from app.core.enums import UserRole, UserStatus
from app.models import (
    ClientProfile,
    FreelancerPolicy,
    OutboxEvent,
    StoredFile,
    User,
)

B = "/api/v1"


def test_client_registration_login_profile_and_no_role_injection(client, db):
    data = {
        "terms_acceptance": {"accepted": True, "version": "2026-11-12"},
        "email": "newclient@example.com",
        "password": "Password@123",
        "full_name": "New Client",
        "phone": "+84900000000",
    }
    r = client.post(B + "/auth/register-client", json=data)
    assert r.status_code == 201, r.text
    u = db.query(User).filter_by(email=data["email"]).one()
    assert u.role == UserRole.CLIENT and u.email_verified_at is None
    assert db.query(ClientProfile).filter_by(user_id=u.id).one().full_name == "New Client"
    assert client.post(B + "/auth/register-client", json=data).status_code == 409
    assert (
        client.post(B + "/auth/register-client", json={**data, "role": "ADMIN"}).status_code == 422
    )
    assert (
        client.post(
            B + "/auth/login", json={"email": data["email"], "password": data["password"]}
        ).status_code
        == 200
    )


def test_pending_company_gets_only_onboarding_access(client, db, make_user):
    from app.core.security import hash_password

    u = make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL)
    u.password_hash = hash_password("Password@123")
    db.commit()
    r = client.post(
        B + "/auth/onboarding-token", json={"email": u.email, "password": "Password@123"}
    )
    assert r.status_code == 200, r.text
    h = {"Authorization": "Bearer " + r.json()["data"]["access_token"]}
    assert client.get(B + "/client-accounts/eligibility/me", headers=h).status_code == 200
    assert client.get(B + "/auth/me", headers=h).status_code == 401
    assert client.get(B + "/freelance-projects", headers=h).status_code == 401


def test_contact_change_requires_password_and_clears_proof(client, db, make_user, auth_headers):
    u = make_user(UserRole.CLIENT)
    u.email_verified_at = datetime(2026, 1, 1)
    u.phone_verified_at = datetime(2026, 1, 1)
    db.commit()
    assert (
        client.patch(
            B + "/auth/contacts",
            headers=auth_headers(u),
            json={"password": "bad", "phone": "+84900000000"},
        ).status_code
        == 401
    )
    r = client.patch(
        B + "/auth/contacts",
        headers=auth_headers(u),
        json={"password": "Password@123", "phone": "+84900000000"},
    )
    assert r.status_code == 200, r.text
    db.refresh(u)
    assert u.phone_verified_at is None and u.email_verified_at is not None


def test_upload_stays_pending_and_never_has_public_url(
    client, db, make_user, auth_headers, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "FREELANCER_FILE_SCAN_ENABLED", True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    u = make_user(UserRole.CLIENT)
    r = client.post(
        B + "/files",
        headers=auth_headers(u),
        data={"category": "EVIDENCE"},
        files={"file": ("proof.pdf", b"%PDF-1.4 sample", "application/pdf")},
    )
    assert r.status_code == 201, r.text
    f = db.query(StoredFile).one()
    assert f.scan_status == "PENDING"
    assert "storage_key" not in r.json()["data"]
    assert db.query(OutboxEvent).filter_by(event_type="file.scan").count() == 1
    assert client.get(B + f"/files/{f.id}/download", headers=auth_headers(u)).status_code == 409
    assert (
        client.post(
            B + "/files",
            headers=auth_headers(u),
            data={"category": "EVIDENCE"},
            files={"file": ("fake.pdf", b"executable", "application/pdf")},
        ).status_code
        == 400
    )


def test_policy_revision_conflict_and_role_boundary(client, db, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    other = make_user(UserRole.CLIENT)
    values = client.get(B + "/admin/freelancer-policy", headers=auth_headers(admin)).json()["data"][
        "values"
    ]
    values["review_period_seconds"] = 86400
    data = {"expected_revision": 0, "values": values, "reason": "School policy"}
    assert (
        client.put(
            B + "/admin/freelancer-policy", headers=auth_headers(other), json=data
        ).status_code
        == 403
    )
    assert (
        client.put(
            B + "/admin/freelancer-policy", headers=auth_headers(admin), json=data
        ).status_code
        == 200
    )
    assert (
        client.put(
            B + "/admin/freelancer-policy", headers=auth_headers(admin), json=data
        ).status_code
        == 409
    )
    assert db.query(FreelancerPolicy).one().revision == 1


def test_retired_business_approval_is_removed(client):
    assert client.post(B + "/admin/business-verifications/1/approve", json={}).status_code == 404


def test_admin_cannot_create_duplicate_mou_flow(client, db, make_user, auth_headers):
    from tests.freelancer.test_group_a_api import company, mou_payload, stored

    u = make_user(UserRole.COMPANY)
    a = make_user(UserRole.ADMIN)
    c = company(db, u, business_status="VERIFIED")
    f = stored(db, a)
    body = mou_payload(c, f)
    url = B + f"/admin/companies/{c.id}/mou-agreements"
    assert client.post(url, headers=auth_headers(u), json=body).status_code == 405
    assert client.post(url, headers=auth_headers(a), json=body).status_code == 405
