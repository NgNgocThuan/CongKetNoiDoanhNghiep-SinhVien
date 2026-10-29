from datetime import date, timedelta

from app.core.config import settings
from app.core.enums import ApplicationStatus, JobStatus, UserRole
from app.models import Application, Company, Faculty, Job, JobType, Major, Student
from app.services import cv_service

BASE = "/api/v1/cvs"


def make_student(db, make_user, *, code="CV001"):
    user = make_user(UserRole.STUDENT, email=f"{code.lower()}@test.com")
    faculty = Faculty(code=f"F-{code}", name=f"Faculty {code}")
    db.add(faculty)
    db.flush()
    major = Major(faculty_id=faculty.id, code=f"M-{code}", name=f"Major {code}")
    db.add(major)
    db.flush()
    student = Student(
        user_id=user.id,
        student_code=code,
        full_name=f"Student {code}",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="K65",
        gpa=3.75,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return user, student


def test_online_cv_prefills_official_data_and_keeps_one_default(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    user, _ = make_student(db, make_user)
    headers = auth_headers(user)

    first = client.post(
        f"{BASE}/online",
        json={
            "title": "CV Online",
            "content_json": {
                "official": {"gpa": 0},
                "skills": ["Python"],
            },
        },
        headers=headers,
    )
    assert first.status_code == 201
    first_body = first.json()
    assert first_body["is_default"] is True
    assert first_body["content_json"]["official"]["student_code"] == "CV001"
    assert first_body["content_json"]["official"]["gpa"] == 3.75

    uploaded = client.post(
        f"{BASE}/upload",
        data={"title": "Uploaded CV"},
        files={"file": ("resume.pdf", b"%PDF-test", "application/pdf")},
        headers=headers,
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["is_default"] is False

    made_default = client.post(
        f"{BASE}/{uploaded.json()['id']}/set-default", headers=headers
    )
    assert made_default.status_code == 200
    listing = client.get(f"{BASE}/me", headers=headers).json()
    assert sum(item["is_default"] for item in listing) == 1
    assert listing[0]["id"] == uploaded.json()["id"]

    assert client.delete(
        f"{BASE}/{uploaded.json()['id']}", headers=headers
    ).status_code == 204
    after_delete = client.get(f"{BASE}/me", headers=headers).json()
    assert [item["id"] for item in after_delete] == [first_body["id"]]
    assert after_delete[0]["is_default"] is True


def test_upload_validation_update_ownership_and_ai_analysis(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    user, _ = make_student(db, make_user, code="CV001")
    other_user, _ = make_student(db, make_user, code="CV002")
    headers = auth_headers(user)

    invalid = client.post(
        f"{BASE}/upload",
        data={"title": "Bad"},
        files={"file": ("resume.txt", b"text", "text/plain")},
        headers=headers,
    )
    assert invalid.status_code == 400

    cv = client.post(
        f"{BASE}/online",
        json={"title": "AI CV", "content_json": {"summary": "Backend"}},
        headers=headers,
    ).json()
    assert client.put(
        f"{BASE}/{cv['id']}",
        json={"title": "Hacked"},
        headers=auth_headers(other_user),
    ).status_code == 404

    monkeypatch.setattr(
        cv_service.cv_parser,
        "parse_cv",
        lambda db, model: {"skills": ["Python"], "cv_id": model.id},
    )
    analyzed = client.post(f"{BASE}/{cv['id']}/analyze", headers=headers)
    assert analyzed.status_code == 200
    assert analyzed.json()["parsed_json"]["skills"] == ["Python"]


def test_company_download_requires_application(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    student_user, student = make_student(db, make_user)
    upload = client.post(
        f"{BASE}/upload",
        data={"title": "Application CV"},
        files={"file": ("resume.pdf", b"%PDF-private", "application/pdf")},
        headers=auth_headers(student_user),
    )
    cv_id = upload.json()["id"]

    company_user = make_user(UserRole.COMPANY, email="company@test.com")
    company = Company(user_id=company_user.id, name="Acme", tax_code="TAX-CV")
    job_type = JobType(code="INTERN-CV", name="Intern")
    db.add_all([company, job_type])
    db.flush()
    job = Job(
        company_id=company.id,
        title="Backend Intern",
        position="Backend",
        job_type_id=job_type.id,
        description="Build APIs",
        deadline=date.today() + timedelta(days=30),
        status=JobStatus.APPROVED,
    )
    db.add(job)
    db.commit()

    denied = client.get(f"{BASE}/{cv_id}/download", headers=auth_headers(company_user))
    assert denied.status_code == 404

    db.add(
        Application(
            student_id=student.id,
            job_id=job.id,
            cv_id=cv_id,
            current_status=ApplicationStatus.APPLIED,
        )
    )
    db.commit()
    allowed = client.get(f"{BASE}/{cv_id}/download", headers=auth_headers(company_user))
    assert allowed.status_code == 200
    assert allowed.content == b"%PDF-private"
