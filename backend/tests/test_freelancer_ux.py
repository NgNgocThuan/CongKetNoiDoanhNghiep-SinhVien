from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.enums import UserRole
from app.models import FreelanceProjectSkill, Skill, User

B = "/api/v1"
ACCEPTANCE = {"accepted": True, "version": "2026-11-12"}


@pytest.mark.parametrize("endpoint,extra", [
    ("register-client", {"full_name": "Client"}),
    ("register-company", {"company_name": "Example", "tax_code": "0123456789"}),
])
def test_registration_requires_explicit_versioned_consent(client, db, endpoint, extra):
    body = {"email": "consent@example.com", "password": "Password@123", **extra}
    path = B + "/auth/" + endpoint
    for invalid in (None, {"accepted": False, "version": "2026-11-12"},
                    {"accepted": "true", "version": "2026-11-12"},
                    {"accepted": True, "version": "old"}):
        data = body if invalid is None else {**body, "terms_acceptance": invalid}
        assert client.post(path, json=data).status_code == 422
    assert db.scalar(select(User).where(User.email == body["email"])) is None
    result = client.post(path, json={**body, "terms_acceptance": ACCEPTANCE})
    assert result.status_code == 201, result.text
    user = db.scalar(select(User).where(User.email == body["email"]))
    assert user.registration_terms_version == ACCEPTANCE["version"]
    assert user.registration_terms_accepted_at is not None
    assert user.escrow_terms_accepted_at is None


def test_escrow_gate_persists_once_and_guards_direct_project_api(client, db, make_user, auth_headers):
    owner = make_user(UserRole.CLIENT)
    owner.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    headers = auth_headers(owner)
    path = B + "/auth/escrow-terms"
    assert client.get(path, headers=headers).json()["data"]["has_accepted_escrow_terms"] is False
    assert client.post(B + "/freelance-projects", headers=headers, json={"title": "Draft"}).status_code == 403
    assert client.post(path, headers=headers, json={**ACCEPTANCE, "accepted": False}).status_code == 422
    first = client.post(path, headers=headers, json=ACCEPTANCE)
    assert first.status_code == 200, first.text
    second = client.post(path, headers=headers, json=ACCEPTANCE)
    assert second.json()["data"]["accepted_at"] == first.json()["data"]["accepted_at"]
    assert client.get(path, headers=headers).json()["data"]["has_accepted_escrow_terms"] is True
    assert client.post(B + "/freelance-projects", headers=headers, json={"title": "Draft"}).status_code == 201
    student = make_user(UserRole.STUDENT)
    assert client.post(path, headers=auth_headers(student), json=ACCEPTANCE).status_code == 403


def test_skill_creation_reuses_id_and_links_project_without_admin(client, db, make_user, auth_headers):
    owner = make_user(UserRole.CLIENT)
    owner.email_verified_at = datetime.now(timezone.utc)
    owner.escrow_terms_accepted_at = datetime.now(timezone.utc)
    db.commit()
    headers = auth_headers(owner)
    path = B + "/catalog/skill-tags"
    first = client.post(path, headers=headers, json={"name": "  Prompt   Engineering  "})
    assert first.status_code == 200, first.text
    skill = first.json()
    second = client.post(path, headers=headers, json={"name": "PROMPT ENGINEERING"})
    assert second.json()["id"] == skill["id"]
    assert skill["category"] == "OTHER" and skill["is_active"]
    assert client.post(path, headers=headers, json={"name": "<script>"}).status_code == 400
    assert client.get(B + "/catalog/skills?q=prompt", headers=headers).json()["items"][0]["id"] == skill["id"]
    result = client.post(B + "/freelance-projects", headers=headers, json={"title": "Draft", "skill_ids": [skill["id"]]})
    assert result.status_code == 201, result.text
    assert db.scalar(select(FreelanceProjectSkill.skill_id)) == skill["id"]
    db.get(Skill, skill["id"]).is_active = False
    db.commit()
    assert client.post(path, headers=headers, json={"name": "prompt engineering"}).status_code == 400


def test_bank_catalog_is_available_without_provider_call(client, make_user, auth_headers):
    result = client.get(B + "/finance/banks", headers=auth_headers(make_user()))
    assert result.status_code == 200, result.text
    banks = result.json()
    assert len(banks) >= 54
    assert len({b["bin"] for b in banks}) == len(banks)
    assert next(b for b in banks if b["code"] == "MB")["bin"] == "970422"
