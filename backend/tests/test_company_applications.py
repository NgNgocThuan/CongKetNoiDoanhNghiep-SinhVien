"""Test: Kanban ứng viên (đổi trạng thái, lịch sử, chi tiết, lọc) và lời mời ứng tuyển."""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.enums import (
    ApplicationStatus,
    CVType,
    InvitationStatus,
    UserRole,
    VerificationStatus,
)
from app.models import (
    CV,
    Application,
    ApplicationStatusLog,
    Base,
    Company,
    Invitation,
    Job,
    Notification,
    Student,
    StudentExperience,
    StudentProfile,
)
from app.schemas.applications import ApplicationRead, StatusLogRead

APP_URL = "/api/v1/company/applications"
INV_URL = "/api/v1/invitations"


# --------------------------------------------------------------------------- helpers
@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    """Không gửi email thật khi BackgroundTasks chạy."""
    monkeypatch.setattr("app.services.email_service.send_email_task", lambda *a, **k: None, raising=False)


@pytest.fixture()
def build(db):
    """Tạo bản ghi bất kỳ: tự điền cột NOT NULL còn thiếu và tự tạo bản ghi cha cho khóa ngoại
    (Faculty, Major, JobType... không cần biết trước trường)."""
    counter = {"n": 0}
    models = {m.local_table.name: m.class_ for m in Base.registry.mappers}

    def _value(col):
        counter["n"] += 1
        n = counter["n"]
        enums = getattr(col.type, "enums", None)
        if enums:
            return enums[0]
        try:
            py = col.type.python_type
        except NotImplementedError:
            return f"{col.name}{n}"
        if py is str:
            text = f"{col.name}{n}"
            length = getattr(col.type, "length", None)
            return text[:length] if length else text
        if py is bool:
            return False
        if py is int:
            return 1
        if py is float:
            return 1.0
        if py is datetime:
            return datetime.utcnow()
        if py is date:
            return date.today() + timedelta(days=30)
        if py is dict:
            return {}
        from decimal import Decimal

        if py is Decimal:
            return Decimal("1")
        return f"{col.name}{n}"

    def _build(model, **kwargs):
        for col in model.__table__.columns:
            key = col.key
            if key in kwargs or col.nullable or col.default is not None or col.server_default is not None:
                continue
            if col.foreign_keys:
                parent_table = next(iter(col.foreign_keys)).column.table
                kwargs[key] = _build(models[parent_table.name]).id
            elif col.primary_key:
                continue
            else:
                kwargs[key] = _value(col)
        obj = model(**kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    return _build


@pytest.fixture()
def make_company(db, make_user):
    counter = {"n": 0}

    def _make():
        counter["n"] += 1
        user = make_user(UserRole.COMPANY)
        company = Company(
            user_id=user.id,
            name=f"Công ty {counter['n']}",
            tax_code=f"02000000{counter['n']}",
            verification_status=VerificationStatus.APPROVED,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return user, company

    return _make


@pytest.fixture()
def make_student(db, make_user, build):
    """open=None: không có profile; True/False: có profile với is_open_to_work tương ứng."""

    def _make(open=None, show_contact=False):
        user = make_user(UserRole.STUDENT)
        student = build(Student, user_id=user.id)
        if open is not None:
            db.add(
                StudentProfile(
                    student_id=student.id,
                    is_open_to_work=open,
                    show_contact=show_contact,
                    contact_email="lienhe@test.com",
                    contact_phone="0900000000",
                )
            )
            db.commit()
            db.refresh(student)
        return user, student

    return _make


@pytest.fixture()
def make_job(build):
    return lambda company: build(Job, company_id=company.id)


@pytest.fixture()
def make_application(db, build):
    def _make(student, job, status=ApplicationStatus.APPLIED):
        cv = build(CV, student_id=student.id, type=CVType.UPLOADED)
        application = Application(student_id=student.id, job_id=job.id, cv_id=cv.id, current_status=status)
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    return _make


# --------------------------------------------------------------------------- schema
def test_application_read_validates_from_model(make_company, make_student, make_job, make_application):
    _, company = make_company()
    _, student = make_student(open=True)
    application = make_application(student, make_job(company))
    data = ApplicationRead.model_validate(application)
    assert data.applied_at == application.applied_at


def test_status_log_read_validates_from_model(db, make_company, make_student, make_job, make_application):
    _, company = make_company()
    _, student = make_student(open=True)
    application = make_application(student, make_job(company))
    log = ApplicationStatusLog(application_id=application.id, old_status="APPLIED", new_status="SCREENING")
    db.add(log)
    db.commit()
    db.refresh(log)
    data = StatusLogRead.model_validate(log)
    assert data.new_status == "SCREENING" and data.changed_at is not None


# --------------------------------------------------------------------------- Kanban
def test_change_status_writes_log_and_notifies(
    client, db, make_company, make_student, make_job, make_application, auth_headers
):
    company_user, company = make_company()
    student_user, student = make_student(open=True)
    application = make_application(student, make_job(company))

    response = client.put(
        f"{APP_URL}/{application.id}/status",
        json={"status": "SCREENING", "note": "Hồ sơ phù hợp"},
        headers=auth_headers(company_user),
    )
    assert response.status_code == 200, response.text
    assert response.json()["current_status"] == "SCREENING"

    log = db.scalars(select(ApplicationStatusLog).where(ApplicationStatusLog.application_id == application.id)).one()
    assert (log.old_status, log.new_status) == ("APPLIED", "SCREENING")
    assert log.changed_by == company_user.id
    assert log.note == "Hồ sơ phù hợp"

    notification = db.scalars(select(Notification).where(Notification.user_id == student_user.id)).one()
    assert notification.type == "APPLICATION_STATUS"


def test_invalid_transition_is_rejected(client, db, make_company, make_student, make_job, make_application, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=True)
    application = make_application(student, make_job(company))

    response = client.put(
        f"{APP_URL}/{application.id}/status", json={"status": "OFFER"}, headers=auth_headers(company_user)
    )
    assert response.status_code == 400
    assert db.scalars(select(ApplicationStatusLog)).first() is None


def test_closed_application_cannot_change(client, make_company, make_student, make_job, make_application, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=True)
    application = make_application(student, make_job(company), status=ApplicationStatus.REJECTED)
    response = client.put(
        f"{APP_URL}/{application.id}/status", json={"status": "SCREENING"}, headers=auth_headers(company_user)
    )
    assert response.status_code == 409


def test_history_returns_logs(client, make_company, make_student, make_job, make_application, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=True)
    application = make_application(student, make_job(company))
    headers = auth_headers(company_user)
    client.put(f"{APP_URL}/{application.id}/status", json={"status": "SCREENING"}, headers=headers)
    client.put(f"{APP_URL}/{application.id}/status", json={"status": "SHORTLISTED"}, headers=headers)

    response = client.get(f"{APP_URL}/{application.id}/history", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert [(i["old_status"], i["new_status"]) for i in body] == [
        ("APPLIED", "SCREENING"),
        ("SCREENING", "SHORTLISTED"),
    ]
    assert body[0]["changed_by"] == company_user.id and body[0]["changed_at"]


def test_detail_hides_contact_by_default(client, make_company, make_student, make_job, make_application, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=True, show_contact=False)
    application = make_application(student, make_job(company))

    response = client.get(f"{APP_URL}/{application.id}", headers=auth_headers(company_user))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["applied_at"]
    assert body["contact_email"] is None and body["contact_phone"] is None
    assert "profile" not in body["student"]


def test_detail_shows_contact_when_allowed(client, make_company, make_student, make_job, make_application, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=True, show_contact=True)
    application = make_application(student, make_job(company))

    body = client.get(f"{APP_URL}/{application.id}", headers=auth_headers(company_user)).json()
    assert body["contact_email"] == "lienhe@test.com"
    assert body["contact_phone"] == "0900000000"


def test_other_company_cannot_see_application(
    client, make_company, make_student, make_job, make_application, auth_headers
):
    _, company = make_company()
    other_user, _ = make_company()
    _, student = make_student(open=True)
    application = make_application(student, make_job(company))

    headers = auth_headers(other_user)
    assert client.get(f"{APP_URL}/{application.id}", headers=headers).status_code == 404
    assert (
        client.put(f"{APP_URL}/{application.id}/status", json={"status": "SCREENING"}, headers=headers).status_code
        == 404
    )


def test_list_applications_and_experience_filter(
    client, db, make_company, make_student, make_job, make_application, auth_headers
):
    company_user, company = make_company()
    job = make_job(company)
    _, experienced = make_student(open=True)
    _, newbie = make_student(open=True)
    make_application(experienced, job)
    make_application(newbie, job)
    db.add(
        StudentExperience(
            student_id=experienced.id,
            company_name="ABC",
            position="Intern",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),  # 12 tháng
        )
    )
    db.commit()
    headers = auth_headers(company_user)

    everyone = client.get(APP_URL, params={"job_id": job.id}, headers=headers)
    assert everyone.status_code == 200, everyone.text
    assert everyone.json()["total"] == 2

    filtered = client.get(APP_URL, params={"job_id": job.id, "min_experience_months": 6}, headers=headers).json()
    assert [i["student_id"] for i in filtered["items"]] == [experienced.id]
    assert filtered["items"][0]["student"]["experience_months"] == 12

    assert client.get(APP_URL, params={"job_id": job.id, "min_experience_months": 24}, headers=headers).json()["total"] == 0


# --------------------------------------------------------------------------- Lời mời
def test_invite_open_student(client, db, make_company, make_student, make_job, auth_headers):
    company_user, company = make_company()
    student_user, student = make_student(open=True)
    job = make_job(company)

    response = client.post(
        INV_URL, json={"job_id": job.id, "student_id": student.id, "message": "Mời bạn"}, headers=auth_headers(company_user)
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "PENDING"
    assert db.scalars(select(Notification).where(Notification.user_id == student_user.id)).one().type == "INVITATION"


def test_invite_closed_student_rejected(client, make_company, make_student, make_job, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=False)
    response = client.post(
        INV_URL, json={"job_id": make_job(company).id, "student_id": student.id}, headers=auth_headers(company_user)
    )
    assert response.status_code == 400


def test_invite_student_without_profile_rejected(client, make_company, make_student, make_job, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=None)
    response = client.post(
        INV_URL, json={"job_id": make_job(company).id, "student_id": student.id}, headers=auth_headers(company_user)
    )
    assert response.status_code == 400


def test_duplicate_invitation_conflict(client, make_company, make_student, make_job, auth_headers):
    company_user, company = make_company()
    _, student = make_student(open=True)
    payload = {"job_id": make_job(company).id, "student_id": student.id}
    headers = auth_headers(company_user)
    assert client.post(INV_URL, json=payload, headers=headers).status_code == 201
    assert client.post(INV_URL, json=payload, headers=headers).status_code == 409


def test_student_declines_invitation(client, db, make_company, make_student, make_job, auth_headers):
    company_user, company = make_company()
    student_user, student = make_student(open=True)
    created = client.post(
        INV_URL, json={"job_id": make_job(company).id, "student_id": student.id}, headers=auth_headers(company_user)
    ).json()

    response = client.post(f"{INV_URL}/{created['id']}/decline", headers=auth_headers(student_user))
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "DECLINED"
    invitation = db.get(Invitation, created["id"])
    db.refresh(invitation)
    assert invitation.status == InvitationStatus.DECLINED and invitation.responded_at is not None