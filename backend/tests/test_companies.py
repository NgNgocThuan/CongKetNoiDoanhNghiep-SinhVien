"""Test hồ sơ doanh nghiệp: xem, cập nhật, giấy tờ, hồ sơ công khai, phân quyền."""
import pytest

from app.core.config import settings
from app.core.enums import UserRole, VerificationStatus
from app.models.company import Company

URL = "/api/v1/companies"


@pytest.fixture()
def make_company(db, make_user):
    counter = {"n": 0}

    def _make(status: VerificationStatus = VerificationStatus.PENDING):
        counter["n"] += 1
        user = make_user(UserRole.COMPANY)
        company = Company(
            user_id=user.id,
            name=f"Công ty {counter['n']}",
            tax_code=f"010000000{counter['n']}",
            verification_status=status,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        db.refresh(user)
        return user, company

    return _make


def test_company_gets_own_profile(client, make_company, auth_headers):
    user, _ = make_company()
    response = client.get(f"{URL}/me", headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "PENDING"
    assert body["documents"] == []


def test_student_cannot_access_company_me(client, make_user, auth_headers):
    student = make_user(UserRole.STUDENT)
    assert client.get(f"{URL}/me", headers=auth_headers(student)).status_code == 403
    assert client.get(f"{URL}/me").status_code == 401


def test_company_updates_profile(client, make_company, auth_headers):
    user, _ = make_company()
    response = client.put(
        f"{URL}/me",
        json={"address": "Hà Nội", "company_size": "11-50", "tech_stack": "Python, FastAPI"},
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "Hà Nội"
    assert body["company_size"] == "11-50"
    assert body["tax_code"]  # không bị đổi


def test_update_with_unknown_industry_is_bad_request(client, make_company, auth_headers):
    user, _ = make_company()
    response = client.put(f"{URL}/me", json={"industry_id": 9999}, headers=auth_headers(user))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_upload_and_delete_document(client, make_company, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    user, _ = make_company()
    headers = auth_headers(user)

    created = client.post(
        f"{URL}/me/documents",
        data={"doc_type": "BUSINESS_LICENSE"},
        files={"file": ("giay-phep.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers=headers,
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]
    assert client.get(f"{URL}/me", headers=headers).json()["documents"][0]["id"] == doc_id

    assert client.delete(f"{URL}/me/documents/{doc_id}", headers=headers).status_code == 204
    assert client.get(f"{URL}/me", headers=headers).json()["documents"] == []


def test_upload_rejects_bad_extension(client, make_company, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    user, _ = make_company()
    response = client.post(
        f"{URL}/me/documents",
        data={"doc_type": "OTHER"},
        files={"file": ("virus.exe", b"x", "application/octet-stream")},
        headers=auth_headers(user),
    )
    assert response.status_code == 400


def test_cannot_delete_other_company_document(client, make_company, auth_headers, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    owner, _ = make_company()
    other, _ = make_company()
    doc_id = client.post(
        f"{URL}/me/documents",
        data={"doc_type": "TAX_CERTIFICATE"},
        files={"file": ("a.pdf", b"%PDF", "application/pdf")},
        headers=auth_headers(owner),
    ).json()["id"]

    response = client.delete(f"{URL}/me/documents/{doc_id}", headers=auth_headers(other))
    assert response.status_code == 404


def test_public_profile_only_for_approved(client, make_company, make_user, auth_headers):
    student = make_user(UserRole.STUDENT)
    _, pending = make_company(VerificationStatus.PENDING)
    _, approved = make_company(VerificationStatus.APPROVED)

    assert client.get(f"{URL}/{pending.id}", headers=auth_headers(student)).status_code == 404

    response = client.get(f"{URL}/{approved.id}", headers=auth_headers(student))
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == approved.name
    assert "tax_code" not in body
    assert "verification_status" not in body