"""Regression tests for bugs found while integrating TV1-TV5."""

from datetime import date, datetime
from io import BytesIO

import pytest
from openpyxl import Workbook

from app.core.config import settings
from app.models import CV, Application, InternshipTerm, Job, Student, StudentExperience, TermStudent
from tests.school_factories import domain


@pytest.fixture(autouse=True)
def no_external_effects(monkeypatch):
    monkeypatch.setattr("app.tasks.email_tasks._deliver", lambda *a, **kw: None)
    monkeypatch.setattr(
        "app.services.admin_job_service._safe_parse_job_task", lambda *a, **kw: None
    )


def test_nonfinite_gpa_only_rejects_bad_rows(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    lines = ["student_code,full_name,email,faculty,major,cohort,gpa"]
    for code, gpa in (("BAD", "NaN"), ("INF", "Infinity"), ("GOOD", "3.25")):
        lines.append(
            f"{code},Student,{code.lower()}@test.com,{d.faculty.code},{d.major.code},K65,{gpa}"
        )
    response = client.post(
        "/api/v1/admin/students/import",
        headers=auth_headers(d.admin),
        files={"file": ("students.csv", "\n".join(lines).encode())},
    )
    assert response.status_code == 201, response.text
    batch = response.json()["batch"]
    assert batch["success_rows"] == 1 and batch["failed_rows"] == 2
    assert [e["row"] for e in batch["errors"]] == [2, 3]


@pytest.mark.parametrize(
    "filename,content", [("bad.xlsx", b"not zip"), ("bad.csv", b"\xff\xfe"), ("empty.csv", b"")]
)
def test_malformed_import_is_400(client, make_user, auth_headers, filename, content):
    from app.core.enums import UserRole

    result = client.post(
        "/api/v1/admin/students/import",
        headers=auth_headers(make_user(UserRole.ADMIN)),
        files={"file": (filename, content)},
    )
    assert result.status_code == 400
    assert result.json()["error"]["code"] == "BAD_REQUEST"


def test_import_reports_actual_excel_row_after_blank(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    book = Workbook()
    book.active.append(["student_code", "full_name", "email", "faculty", "major", "cohort", "gpa"])
    book.active.append([None] * 7)
    book.active.append(["BAD", "Bad", "bad@test.com", d.faculty.code, d.major.code, "K65", "NaN"])
    out = BytesIO()
    book.save(out)
    response = client.post(
        "/api/v1/admin/students/import",
        headers=auth_headers(d.admin),
        files={"file": ("students.xlsx", out.getvalue())},
    )
    assert response.status_code == 201
    assert response.json()["batch"]["errors"][0]["row"] == 3


@pytest.mark.parametrize("target", ["skill", "profile", "cv"])
def test_required_update_fields_reject_null(client, db, make_user, auth_headers, target):
    d = domain(db, make_user)
    if target == "skill":
        url, headers, data = (
            f"/api/v1/catalog/skills/{d.skill.id}",
            auth_headers(d.admin),
            {"name": None},
        )
    elif target == "profile":
        url, headers, data = (
            "/api/v1/students/me/profile",
            auth_headers(d.student_user),
            {"show_gpa": None},
        )
    else:
        url, headers, data = f"/api/v1/cvs/{d.cv.id}", auth_headers(d.student_user), {"title": None}
    result = client.put(url, headers=headers, json=data)
    assert result.status_code == 422, result.text


def test_term_jobs_hide_expired_for_student(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    term = InternshipTerm(
        name="Term",
        semester="1",
        academic_year="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        created_by=d.admin.id,
    )
    db.add(term)
    db.flush()
    db.add(TermStudent(term_id=term.id, student_id=d.student.id))
    d.job.term_id = term.id
    d.job.deadline = date(2000, 1, 1)
    db.commit()
    url = f"/api/v1/internship-terms/{term.id}/jobs"
    assert client.get(url, headers=auth_headers(d.student_user)).json()["total"] == 0
    assert client.get(url, headers=auth_headers(d.admin)).json()["total"] == 1


def test_employer_privacy_is_checked_in_list_detail_and_filter(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    app = Application(student_id=d.student.id, job_id=d.job.id, cv_id=d.cv.id)
    db.add(app)
    db.commit()
    headers = auth_headers(d.company_user)
    base = "/api/v1/company/applications"
    for url in (f"{base}/{app.id}", f"{base}?job_id={d.job.id}"):
        result = client.get(url, headers=headers)
        assert result.status_code == 200, result.text
        item = result.json() if "?" not in url else result.json()["items"][0]
        assert item["student"]["gpa"] is None
        assert item["contact_email"] is None and item["contact_phone"] is None
        assert item["student"]["skills"] == ["Python"]
    assert client.get(f"{base}?job_id={d.job.id}&min_gpa=1", headers=headers).json()["total"] == 0
    d.profile.show_gpa = True
    db.commit()
    assert client.get(f"{base}?job_id={d.job.id}&min_gpa=1", headers=headers).json()["total"] == 1


def test_experience_filter_counts_before_pagination(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    db.add(
        StudentExperience(
            student_id=d.student.id,
            company_name="Old",
            position="Dev",
            start_date=date(2020, 1, 1),
            end_date=date(2022, 1, 1),
        )
    )
    db.add(
        Application(
            student_id=d.student.id, job_id=d.job.id, cv_id=d.cv.id, applied_at=datetime(2025, 1, 1)
        )
    )
    user = make_user()
    student = Student(
        user_id=user.id,
        student_code="S2",
        full_name="Newbie",
        faculty_id=d.faculty.id,
        major_id=d.major.id,
        cohort="K65",
    )
    db.add(student)
    db.flush()
    cv = CV(student_id=student.id, title="CV", type="ONLINE", content_json={})
    db.add(cv)
    db.flush()
    db.add(
        Application(
            student_id=student.id, job_id=d.job.id, cv_id=cv.id, applied_at=datetime(2025, 2, 1)
        )
    )
    db.commit()
    url = f"/api/v1/company/applications?job_id={d.job.id}&min_experience_months=12&size=1"
    first = client.get(url, headers=auth_headers(d.company_user))
    assert first.status_code == 200, first.text
    assert first.json()["total"] == first.json()["pages"] == 1
    assert first.json()["items"][0]["student_id"] == d.student.id
    second = client.get(url + "&page=2", headers=auth_headers(d.company_user)).json()
    assert second["total"] == 1 and second["items"] == []


def test_snapshot_download_uses_application_and_checks_company(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    d = domain(db, make_user)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    (tmp_path / "old.json").write_text('{"version":"old"}')
    (tmp_path / "new.json").write_text('{"version":"new"}')
    other_job = Job(
        company_id=d.company.id,
        title="Second",
        position="Dev",
        job_type_id=d.job_type.id,
        description="D",
        deadline=d.job.deadline,
        status="APPROVED",
    )
    db.add(other_job)
    db.flush()
    old = Application(
        student_id=d.student.id,
        job_id=d.job.id,
        cv_id=d.cv.id,
        cv_snapshot_url="old.json",
        applied_at=datetime(2025, 1, 1),
    )
    new = Application(
        student_id=d.student.id,
        job_id=other_job.id,
        cv_id=d.cv.id,
        cv_snapshot_url="new.json",
        applied_at=datetime(2025, 2, 1),
    )
    db.add_all([old, new])
    db.commit()
    for app, version in ((old, "old"), (new, "new")):
        url = f"/api/v1/company/applications/{app.id}/cv"
        assert client.get(url, headers=auth_headers(d.company_user)).json() == {"version": version}
        assert client.get(url, headers=auth_headers(d.other_user)).status_code == 404
        assert client.get(url, headers=auth_headers(d.student_user)).status_code == 403
    assert (
        client.get(
            f"/api/v1/cvs/{d.cv.id}/download", headers=auth_headers(d.company_user)
        ).status_code
        == 409
    )


def test_end_to_end_activation_moderation_invitation_hiring_and_result(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    import re

    from sqlalchemy import select

    from app.models import Student

    d = domain(db, make_user)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    delivered = []
    monkeypatch.setattr(
        "app.tasks.email_tasks._deliver", lambda to, subject, body: delivered.append((to, body))
    )
    admin = auth_headers(d.admin)

    def request(method, url, expected=200, **kwargs):
        response = client.request(method, "/api/v1" + url, **kwargs)
        assert response.status_code == expected, (url, response.status_code, response.text)
        return response

    csv = f"student_code,full_name,email,faculty,major,cohort\nE2E,Student E2E,e2e@test.com,{d.faculty.code},{d.major.code},K65"
    request(
        "POST",
        "/admin/students/import",
        201,
        headers=admin,
        files={"file": ("e2e.csv", csv.encode())},
    )
    token = re.search(
        r"token=([^\"&<]+)", next(body for to, body in delivered if to == "e2e@test.com")
    ).group(1)
    request("POST", "/auth/activate", json={"token": token, "new_password": "Password@123"})
    student_token = request(
        "POST", "/auth/login", json={"email": "e2e@test.com", "password": "Password@123"}
    ).json()["access_token"]
    student_headers = {"Authorization": "Bearer " + student_token}
    student = db.scalar(select(Student).where(Student.student_code == "E2E"))
    request("PUT", "/students/me/profile", headers=student_headers, json={"is_open_to_work": True})
    request(
        "POST", "/students/me/skills", 201, headers=student_headers, json={"skill_id": d.skill.id}
    )
    company = request(
        "POST",
        "/auth/register-company",
        201,
        json={
            "email": "company-e2e@test.com",
            "password": "Password@123",
            "company_name": "E2E Ltd",
            "tax_code": "E2E123",
        },
    ).json()
    request("POST", f"/admin/companies/{company['company_id']}/approve", headers=admin)
    company_token = request(
        "POST", "/auth/login", json={"email": "company-e2e@test.com", "password": "Password@123"}
    ).json()["access_token"]
    company_headers = {"Authorization": "Bearer " + company_token}
    term = request(
        "POST",
        "/internship-terms",
        201,
        headers=admin,
        json={
            "name": "E2E",
            "semester": "1",
            "academic_year": "2026",
            "start_date": "2026-01-01",
            "end_date": "2030-01-01",
        },
    ).json()
    tid = term["id"]
    request(
        "POST",
        f"/internship-terms/{tid}/students",
        201,
        headers=admin,
        json={"student_ids": [student.id]},
    )
    for status in ("OPEN", "ONGOING"):
        request("POST", f"/internship-terms/{tid}/status", headers=admin, json={"status": status})
    job = request(
        "POST",
        "/jobs",
        201,
        headers=company_headers,
        json={
            "title": "E2E Intern",
            "position": "Dev",
            "job_type_id": d.job_type.id,
            "description": "Python",
            "deadline": "2030-01-01",
            "term_id": tid,
            "skills": [{"skill_id": d.skill.id, "is_required": True}],
        },
    ).json()
    jid = job["id"]
    request("POST", f"/jobs/{jid}/submit", headers=company_headers)
    request("POST", f"/admin/jobs/{jid}/approve", headers=admin)
    request("GET", f"/matching/jobs/{jid}/score", headers=student_headers)
    candidates = request("GET", f"/matching/jobs/{jid}/candidates", headers=company_headers).json()
    assert candidates["items"][0]["student_id"] == student.id
    invitation = request(
        "POST",
        "/invitations",
        201,
        headers=company_headers,
        json={"job_id": jid, "student_id": student.id},
    ).json()
    cv = request(
        "POST",
        "/cvs/online",
        201,
        headers=student_headers,
        json={"title": "CV", "content_json": {"bio": "Python"}},
    ).json()
    application = request(
        "POST",
        "/applications",
        201,
        headers=student_headers,
        json={"job_id": jid, "cv_id": cv["id"], "invitation_id": invitation["id"]},
    ).json()
    aid = application["id"]
    request("GET", f"/applications/{aid}", headers=student_headers)
    snapshot = request("GET", f"/company/applications/{aid}/cv", headers=company_headers).json()
    assert snapshot["official"]["student_code"] == "E2E"
    for status in ("SCREENING", "SHORTLISTED", "INTERVIEW", "OFFER", "HIRED"):
        request(
            "PUT",
            f"/company/applications/{aid}/status",
            headers=company_headers,
            json={"status": status, "note": "E2E"},
        )
    logs = request("GET", f"/company/applications/{aid}/history", headers=company_headers).json()
    assert len(logs) == 6 and logs[0]["old_status"] is None
    rid = request("GET", f"/internship-terms/{tid}/results", headers=admin).json()["items"][0]["id"]
    request(
        "PUT",
        f"/internship-terms/results/{rid}/evaluation",
        headers=company_headers,
        json={"evaluation": "Good", "score": 9},
    )
    request(
        "PUT",
        f"/internship-terms/results/{rid}/lecturer-review",
        headers=admin,
        json={"comment": "Good", "score": 9},
    )
    request(
        "POST", f"/internship-terms/results/{rid}/confirm", headers=admin, json={"result": "PASSED"}
    )
    assert request("GET", "/admin/dashboard/overview", headers=admin).json()["hired"] == 1
    assert request("GET", "/admin/exports/applications.xlsx", headers=admin).content.startswith(
        b"PK"
    )
