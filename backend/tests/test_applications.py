from datetime import date, timedelta
from pathlib import Path

from app.core.config import settings
from app.core.enums import InvitationStatus, JobStatus, TermStatus, UserRole
from app.models import (
    Application,
    Company,
    Faculty,
    InternshipTerm,
    Invitation,
    Job,
    JobType,
    Major,
    Notification,
    Student,
)
from app.services import application_service

BASE = "/api/v1/applications"


def make_student(db, make_user, suffix="1"):
    user = make_user(UserRole.STUDENT, email=f"student-{suffix}@test.com")
    faculty = Faculty(code=f"F-APP-{suffix}", name=f"Faculty App {suffix}")
    db.add(faculty)
    db.flush()
    major = Major(faculty_id=faculty.id, code=f"M-APP-{suffix}", name=f"Major App {suffix}")
    db.add(major)
    db.flush()
    student = Student(
        user_id=user.id,
        student_code=f"APP{suffix}",
        full_name=f"Applicant {suffix}",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="K65",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return user, student


def make_job(
    db,
    make_user,
    suffix="1",
    *,
    status=JobStatus.APPROVED,
    deadline=None,
    term_id=None,
):
    company_user = make_user(UserRole.COMPANY, email=f"employer-{suffix}@test.com")
    company = Company(
        user_id=company_user.id,
        name=f"Employer {suffix}",
        tax_code=f"TAX-APP-{suffix}",
    )
    job_type = JobType(code=f"APP-TYPE-{suffix}", name="Intern")
    db.add_all([company, job_type])
    db.flush()
    job = Job(
        company_id=company.id,
        term_id=term_id,
        title=f"Backend Intern {suffix}",
        position="Backend",
        job_type_id=job_type.id,
        description="Build APIs",
        deadline=deadline or date.today() + timedelta(days=30),
        status=status,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return company_user, company, job


def make_online_cv(client, user, auth_headers, title="Application CV"):
    response = client.post(
        "/api/v1/cvs/online",
        json={"title": title, "content_json": {"skills": ["Python"]}},
        headers=auth_headers(user),
    )
    assert response.status_code == 201
    return response.json()


def stub_email(monkeypatch):
    queued = []

    def fake_queue(*args, **kwargs):
        queued.append(kwargs)
        return None

    monkeypatch.setattr(application_service.email_service, "queue_email", fake_queue)
    return queued


def test_apply_copies_cv_logs_notifies_emails_and_blocks_duplicate(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    queued = stub_email(monkeypatch)
    user, student = make_student(db, make_user)
    _, company, job = make_job(db, make_user)
    cv = make_online_cv(client, user, auth_headers)

    response = client.post(
        BASE,
        json={"job_id": job.id, "cv_id": cv["id"], "cover_letter": "I love APIs"},
        headers=auth_headers(user),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["current_status"] == "APPLIED"
    assert body["status_logs"][0]["old_status"] is None
    assert body["status_logs"][0]["new_status"] == "APPLIED"
    assert body["cv_snapshot_url"]
    assert Path(settings.UPLOAD_DIR, body["cv_snapshot_url"]).is_file()
    assert queued[0]["type"] == "APPLY_SUCCESS"
    notice = db.query(Notification).filter_by(user_id=company.user_id).one()
    assert notice.type == "NEW_APPLICATION"

    duplicate = client.post(
        BASE,
        json={"job_id": job.id, "cv_id": cv["id"]},
        headers=auth_headers(user),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_APPLICATION"
    assert db.query(Application).filter_by(student_id=student.id, job_id=job.id).count() == 1


def test_apply_validates_job_cv_term_and_accepts_invitation(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    stub_email(monkeypatch)
    user, student = make_student(db, make_user, "1")
    other_user, _ = make_student(db, make_user, "2")
    own_cv = make_online_cv(client, user, auth_headers, "Own CV")
    other_cv = make_online_cv(client, other_user, auth_headers, "Other CV")

    _, _, draft = make_job(db, make_user, "draft", status=JobStatus.DRAFT)
    assert client.post(
        BASE,
        json={"job_id": draft.id, "cv_id": own_cv["id"]},
        headers=auth_headers(user),
    ).status_code == 400

    _, _, free_job = make_job(db, make_user, "foreign-cv")
    assert client.post(
        BASE,
        json={"job_id": free_job.id, "cv_id": other_cv["id"]},
        headers=auth_headers(user),
    ).status_code == 404

    admin = make_user(UserRole.ADMIN, email="term-admin@test.com")
    term = InternshipTerm(
        name="HK doanh nghiệp",
        semester="HK1",
        academic_year="2026-2027",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        status=TermStatus.OPEN,
        created_by=admin.id,
    )
    db.add(term)
    db.commit()
    _, company, term_job = make_job(db, make_user, "term", term_id=term.id)

    monkeypatch.setattr(
        application_service.internship_service,
        "is_student_in_term",
        lambda db, student_id, term_id: False,
        raising=False,
    )
    blocked = client.post(
        BASE,
        json={"job_id": term_job.id, "cv_id": own_cv["id"]},
        headers=auth_headers(user),
    )
    assert blocked.status_code == 400
    assert blocked.json()["error"]["code"] == "NOT_IN_INTERNSHIP_TERM"

    invitation = Invitation(
        company_id=company.id,
        student_id=student.id,
        job_id=term_job.id,
        status=InvitationStatus.PENDING,
    )
    db.add(invitation)
    db.commit()
    monkeypatch.setattr(
        application_service.internship_service,
        "is_student_in_term",
        lambda db, student_id, term_id: True,
        raising=False,
    )
    accepted = client.post(
        BASE,
        json={
            "job_id": term_job.id,
            "cv_id": own_cv["id"],
            "invitation_id": invitation.id,
        },
        headers=auth_headers(user),
    )
    assert accepted.status_code == 201
    db.refresh(invitation)
    assert invitation.status == InvitationStatus.ACCEPTED
    assert invitation.responded_at is not None


def test_list_detail_ownership_filter_and_withdraw_rules(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    stub_email(monkeypatch)
    user, _ = make_student(db, make_user, "owner")
    other_user, _ = make_student(db, make_user, "other")
    _, _, job = make_job(db, make_user, "tracking")
    cv = make_online_cv(client, user, auth_headers)
    created = client.post(
        BASE,
        json={"job_id": job.id, "cv_id": cv["id"]},
        headers=auth_headers(user),
    ).json()

    listing = client.get(
        f"{BASE}/me", params={"status": "APPLIED"}, headers=auth_headers(user)
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert client.get(
        f"{BASE}/{created['id']}", headers=auth_headers(other_user)
    ).status_code == 404

    withdrawn = client.post(
        f"{BASE}/{created['id']}/withdraw", headers=auth_headers(user)
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["current_status"] == "WITHDRAWN"
    assert withdrawn.json()["status_logs"][-1]["new_status"] == "WITHDRAWN"
    assert client.post(
        f"{BASE}/{created['id']}/withdraw", headers=auth_headers(user)
    ).status_code == 409
