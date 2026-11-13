from app.core.config import settings
from app.models import CV, Invitation
from app.utils.datetime_utils import utcnow
from tests.school_factories import domain


def verified(db, d):
    d.company.business_status = "VERIFIED"
    d.company_user.email_verified_at = utcnow()
    db.commit()


def test_candidate_profile_and_cv_before_invitation_respect_scope_and_consent(client, db, make_user, auth_headers, monkeypatch):
    d = domain(db, make_user)
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    base = f"/api/v1/matching/jobs/{d.job.id}/candidates/{d.student.id}"
    company = auth_headers(d.company_user)
    assert client.get(base + "/profile", headers=company).status_code == 403
    assert client.get(base + "/cv", headers=company).status_code == 403
    verified(db, d)
    response = client.get(base + "/profile", headers=company)
    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == d.student.full_name
    assert response.json()["cv"]["title"] == d.cv.title
    assert response.json()["gpa"] is None
    assert "private@test.com" not in response.text and "0901234567" not in response.text
    assert client.get(base + "/cv", headers=company).status_code == 200
    for endpoint in ("profile", "cv"):
        assert client.get(base + "/" + endpoint, headers=auth_headers(d.other_user)).status_code == 404
        assert client.get(base + "/" + endpoint, headers=auth_headers(d.student_user)).status_code == 403

    # Open-to-work is sufficient; the retired show_cv flag remains false.
    assert not d.profile.show_cv
    assert client.get(base + "/profile", headers=company).json()["cv"]["title"] == d.cv.title
    d.cv.content_json = {"bio": "Python projects", "official": {"gpa": 4, "date_of_birth": "2000-01-01", "phone": "private"}}
    db.commit()
    response = client.get(base + "/cv", headers=company)
    assert response.status_code == 200, response.text
    assert response.json()["content"]["bio"] == "Python projects"
    assert response.json()["content"]["official"]["gpa"] is None
    assert "date_of_birth" not in response.text
    assert db.query(Invitation).count() == 0

    d.profile.is_open_to_work = False
    db.commit()
    assert client.get(base + "/profile", headers=company).status_code == 404
    assert client.get(base + "/cv", headers=company).status_code == 404


def test_cv_uses_default_and_rechecks_uploaded_file_access(client, db, make_user, auth_headers, monkeypatch, tmp_path):
    d = domain(db, make_user)
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    verified(db, d)
    other = CV(student_id=d.student.id, title="Private extra CV", type="ONLINE", content_json={"bio": "Other CV"}, is_default=False)
    db.add(other)
    db.commit()
    base = f"/api/v1/matching/jobs/{d.job.id}/candidates/{d.student.id}"
    headers = auth_headers(d.company_user)
    assert client.get(base + "/profile", headers=headers).json()["cv"]["title"] == d.cv.title
    d.cv.type, d.cv.file_url = "UPLOADED", "shared.pdf"
    (tmp_path / "shared.pdf").write_bytes(b"%PDF-1.4\nshared CV")
    db.commit()
    response = client.get(base + "/cv", headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert "inline" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "private, no-store"
    d.cv.file_url = "../outside.pdf"
    db.commit()
    assert client.get(base + "/cv", headers=headers).status_code == 404
