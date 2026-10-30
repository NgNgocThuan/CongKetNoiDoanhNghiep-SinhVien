from datetime import date, timedelta

from app.core.enums import JobStatus, UserRole
from app.models import Company, Faculty, Job, JobType, Major, Student

BASE = "/api/v1/saved-jobs"


def make_student(db, make_user):
    user = make_user(UserRole.STUDENT, email="saved-student@test.com")
    faculty = Faculty(code="F-SAVED", name="Faculty Saved")
    db.add(faculty)
    db.flush()
    major = Major(faculty_id=faculty.id, code="M-SAVED", name="Major Saved")
    db.add(major)
    db.flush()
    student = Student(
        user_id=user.id,
        student_code="SAVED001",
        full_name="Saved Student",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="K65",
    )
    db.add(student)
    db.commit()
    return user, student


def make_job(db, make_user, *, status=JobStatus.APPROVED, suffix="1"):
    company_user = make_user(UserRole.COMPANY, email=f"company-{suffix}@test.com")
    company = Company(
        user_id=company_user.id, name=f"Company {suffix}", tax_code=f"TAX-SAVED-{suffix}"
    )
    job_type = JobType(code=f"TYPE-{suffix}", name="Intern")
    db.add_all([company, job_type])
    db.flush()
    job = Job(
        company_id=company.id,
        title=f"Backend Intern {suffix}",
        position="Backend",
        job_type_id=job_type.id,
        description="Build APIs",
        deadline=date.today() + timedelta(days=10),
        status=status,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_save_is_idempotent_lists_job_and_unsave_is_idempotent(
    client, db, make_user, auth_headers
):
    user, _ = make_student(db, make_user)
    job = make_job(db, make_user)
    headers = auth_headers(user)

    first = client.post(f"{BASE}/{job.id}", headers=headers)
    second = client.post(f"{BASE}/{job.id}", headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["saved_at"] == second.json()["saved_at"]

    listing = client.get(BASE, params={"page": 1, "size": 10}, headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1
    assert body["items"][0]["job"]["title"] == "Backend Intern 1"
    assert body["items"][0]["job"]["company"]["name"] == "Company 1"

    assert client.delete(f"{BASE}/{job.id}", headers=headers).status_code == 204
    assert client.delete(f"{BASE}/{job.id}", headers=headers).status_code == 204
    assert client.get(BASE, headers=headers).json()["total"] == 0


def test_cannot_save_hidden_job_and_non_student_is_forbidden(
    client, db, make_user, auth_headers
):
    user, _ = make_student(db, make_user)
    draft = make_job(db, make_user, status=JobStatus.DRAFT, suffix="draft")
    assert client.post(
        f"{BASE}/{draft.id}", headers=auth_headers(user)
    ).status_code == 404

    company_user = make_user(UserRole.COMPANY, email="other-company@test.com")
    assert client.get(BASE, headers=auth_headers(company_user)).status_code == 403
