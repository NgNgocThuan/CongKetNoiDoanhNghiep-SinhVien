"""Test tin tuyển dụng: tạo, gửi duyệt, sửa, đóng, tìm kiếm, ẩn tin theo đợt, lượt xem, thống kê, hết hạn."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.enums import (
    ApplicationStatus,
    CVType,
    JobStatus,
    TermStatus,
    UserRole,
    VerificationStatus,
    WorkMode,
)
from app.models import (
    CV,
    Application,
    Company,
    Faculty,
    Industry,
    InternshipTerm,
    Job,
    JobMajor,
    JobSkill,
    JobType,
    JobView,
    Major,
    Skill,
    Student,
    TermStudent,
)
from app.schemas.common import PageParams
from app.services import job_service
from app.utils.datetime_utils import today, utcnow

JOBS = "/api/v1/jobs"


# ---------------------------------------------------------------- Fixture
@pytest.fixture()
def catalog(db):
    faculty = Faculty(code="CNTT", name="Công nghệ thông tin")
    db.add(faculty)
    db.commit()
    se = Major(faculty_id=faculty.id, code="KTPM", name="Kỹ thuật phần mềm")
    info = Major(faculty_id=faculty.id, code="HTTT", name="Hệ thống thông tin")
    intern = JobType(code="INTERN", name="Thực tập")
    full_time = JobType(code="FULL_TIME", name="Toàn thời gian")
    industry = Industry(name="Phần mềm")
    python = Skill(name="Python")
    react = Skill(name="React")
    db.add_all([se, info, intern, full_time, industry, python, react])
    db.commit()
    return SimpleNamespace(
        faculty=faculty,
        se=se,
        info=info,
        intern=intern,
        full_time=full_time,
        industry=industry,
        python=python,
        react=react,
    )


@pytest.fixture()
def make_company(db, make_user):
    counter = {"n": 0}

    def _make(status: VerificationStatus = VerificationStatus.APPROVED):
        counter["n"] += 1
        user = make_user(UserRole.COMPANY)
        company = Company(
            user_id=user.id,
            name=f"Công ty {counter['n']}",
            tax_code=f"020000000{counter['n']}",
            verification_status=status,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        db.refresh(user)
        return user, company

    return _make


@pytest.fixture()
def make_student(db, make_user, catalog):
    counter = {"n": 0}

    def _make(term=None, major=None):
        counter["n"] += 1
        user = make_user(UserRole.STUDENT)
        student = Student(
            user_id=user.id,
            student_code=f"SV{counter['n']:04d}",
            full_name=f"Sinh viên {counter['n']}",
            faculty_id=catalog.faculty.id,
            major_id=(major or catalog.se).id,
            cohort="K65",
        )
        db.add(student)
        db.commit()
        if term is not None:
            db.add(TermStudent(term_id=term.id, student_id=student.id))
            db.commit()
        db.refresh(student)
        db.refresh(user)
        return user, student

    return _make


@pytest.fixture()
def make_term(db, make_user):
    def _make(status: TermStatus = TermStatus.OPEN):
        admin = make_user(UserRole.ADMIN)
        term = InternshipTerm(
            name="Thực tập HK1",
            semester="HK1",
            academic_year="2026-2027",
            start_date=today(),
            end_date=today() + timedelta(days=90),
            status=status,
            created_by=admin.id,
        )
        db.add(term)
        db.commit()
        db.refresh(term)
        return term

    return _make


@pytest.fixture()
def make_job(db, catalog):
    """Tạo tin trực tiếp trong DB (mặc định APPROVED, còn hạn) để dựng tình huống nhanh."""
    counter = {"n": 0}

    def _make(company, *, skills=(), major_ids=(), **overrides) -> Job:
        counter["n"] += 1
        values = {
            "company_id": company.id,
            "title": f"Tin {counter['n']}",
            "position": "Developer",
            "job_type_id": catalog.intern.id,
            "description": "Mô tả công việc",
            "deadline": today() + timedelta(days=30),
            "status": JobStatus.APPROVED,
        }
        values.update(overrides)
        job = Job(**values)
        job.skills = [JobSkill(skill_id=skill_id, is_required=required) for skill_id, required in skills]
        job.majors = [JobMajor(major_id=major_id) for major_id in major_ids]
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    return _make


@pytest.fixture()
def make_application(db):
    counter = {"n": 0}

    def _make(student, job, status: ApplicationStatus = ApplicationStatus.APPLIED) -> Application:
        counter["n"] += 1
        cv = CV(student_id=student.id, title=f"CV {counter['n']}", type=CVType.UPLOADED)
        db.add(cv)
        db.commit()
        application = Application(student_id=student.id, job_id=job.id, cv_id=cv.id, current_status=status)
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    return _make


def job_payload(catalog, **overrides) -> dict:
    data = {
        "title": "Thực tập sinh Backend",
        "position": "Backend Developer",
        "job_type_id": catalog.intern.id,
        "description": "Làm việc với FastAPI",
        "deadline": str(today() + timedelta(days=30)),
        "skills": [
            {"skill_id": catalog.python.id, "is_required": True},
            {"skill_id": catalog.react.id, "is_required": False},
        ],
        "major_ids": [catalog.se.id],
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------- Tạo tin
def test_company_creates_job_as_draft(client, catalog, make_company, auth_headers):
    user, _ = make_company()
    response = client.post(JOBS, json=job_payload(catalog), headers=auth_headers(user))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "DRAFT"
    assert body["view_count"] == 0
    assert body["company"]["name"].startswith("Công ty")
    assert {item["skill_id"]: item["is_required"] for item in body["skills"]} == {
        catalog.python.id: True,
        catalog.react.id: False,
    }
    assert [item["major_id"] for item in body["majors"]] == [catalog.se.id]


def test_unapproved_company_cannot_create_job(client, catalog, make_company, auth_headers):
    user, _ = make_company(VerificationStatus.PENDING)
    response = client.post(JOBS, json=job_payload(catalog), headers=auth_headers(user))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "COMPANY_NOT_APPROVED"


def test_only_company_can_create_job(client, catalog, make_student, auth_headers):
    student_user, _ = make_student()
    assert client.post(JOBS, json=job_payload(catalog), headers=auth_headers(student_user)).status_code == 403
    assert client.post(JOBS, json=job_payload(catalog)).status_code == 401


def test_create_job_validation(client, catalog, make_company, auth_headers):
    headers = auth_headers(make_company()[0])
    yesterday = str(today() - timedelta(days=1))

    assert client.post(JOBS, json=job_payload(catalog, job_type_id=9999), headers=headers).status_code == 400
    assert client.post(JOBS, json=job_payload(catalog, deadline=yesterday), headers=headers).status_code == 400
    assert (
        client.post(JOBS, json=job_payload(catalog, salary_min=20, salary_max=10), headers=headers).status_code == 400
    )
    assert (
        client.post(JOBS, json=job_payload(catalog, skills=[{"skill_id": 9999}]), headers=headers).status_code == 400
    )
    assert client.post(JOBS, json=job_payload(catalog, major_ids=[9999]), headers=headers).status_code == 400
    assert client.post(JOBS, json=job_payload(catalog, term_id=9999), headers=headers).status_code == 400
    duplicated = [{"skill_id": catalog.python.id}, {"skill_id": catalog.python.id}]
    assert client.post(JOBS, json=job_payload(catalog, skills=duplicated), headers=headers).status_code == 422


# ---------------------------------------------------------------- Gửi duyệt, sửa, đóng
def test_submit_for_approval(client, catalog, make_company, auth_headers):
    user, _ = make_company()
    headers = auth_headers(user)
    job_id = client.post(JOBS, json=job_payload(catalog), headers=headers).json()["id"]

    submitted = client.post(f"{JOBS}/{job_id}/submit", headers=headers)
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "PENDING_APPROVAL"

    again = client.post(f"{JOBS}/{job_id}/submit", headers=headers)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVALID_JOB_STATUS"


def test_rejected_job_can_be_resubmitted(client, make_company, make_job, auth_headers):
    user, company = make_company()
    job = make_job(company, status=JobStatus.REJECTED, reject_reason="Thiếu thông tin")
    response = client.post(f"{JOBS}/{job.id}/submit", headers=auth_headers(user))
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_APPROVAL"
    assert response.json()["reject_reason"] is None


def test_editing_approved_job_goes_back_to_pending(client, catalog, make_company, make_job, auth_headers):
    user, company = make_company()
    job = make_job(
        company,
        skills=[(catalog.python.id, True)],
        major_ids=[catalog.se.id],
        approved_at=utcnow(),
    )
    response = client.put(
        f"{JOBS}/{job.id}",
        json={
            "title": "Tiêu đề mới",
            "skills": [{"skill_id": catalog.react.id, "is_required": False}],
            "major_ids": [],
        },
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Tiêu đề mới"
    assert body["status"] == "PENDING_APPROVAL"
    assert body["approved_at"] is None
    assert [item["skill_id"] for item in body["skills"]] == [catalog.react.id]
    assert body["majors"] == []


def test_editing_draft_keeps_status(client, make_company, make_job, auth_headers):
    user, company = make_company()
    job = make_job(company, status=JobStatus.DRAFT)
    response = client.put(f"{JOBS}/{job.id}", json={"quantity": 5}, headers=auth_headers(user))
    assert response.status_code == 200
    assert response.json()["status"] == "DRAFT"
    assert response.json()["quantity"] == 5


def test_update_rejects_null_for_required_field(client, make_company, make_job, auth_headers):
    user, company = make_company()
    job = make_job(company, status=JobStatus.DRAFT)
    response = client.put(f"{JOBS}/{job.id}", json={"title": None}, headers=auth_headers(user))
    assert response.status_code == 400


def test_company_cannot_touch_other_company_job(client, make_company, make_job, auth_headers):
    _, owner_company = make_company()
    other_user, _ = make_company()
    job = make_job(owner_company, status=JobStatus.DRAFT)
    headers = auth_headers(other_user)

    assert client.put(f"{JOBS}/{job.id}", json={"quantity": 2}, headers=headers).status_code == 404
    assert client.post(f"{JOBS}/{job.id}/submit", headers=headers).status_code == 404
    assert client.post(f"{JOBS}/{job.id}/close", headers=headers).status_code == 404
    assert client.get(f"{JOBS}/{job.id}/stats", headers=headers).status_code == 404
    assert client.get(f"{JOBS}/{job.id}", headers=headers).status_code == 404


def test_close_job_and_closed_job_is_locked(client, make_company, make_job, auth_headers):
    user, company = make_company()
    job = make_job(company)
    headers = auth_headers(user)

    closed = client.post(f"{JOBS}/{job.id}/close", headers=headers)
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"

    edit = client.put(f"{JOBS}/{job.id}", json={"quantity": 3}, headers=headers)
    assert edit.status_code == 409
    assert edit.json()["error"]["code"] == "JOB_NOT_EDITABLE"
    assert client.post(f"{JOBS}/{job.id}/close", headers=headers).status_code == 409


# ---------------------------------------------------------------- Tìm kiếm: quy tắc hiển thị
def test_search_returns_only_approved_and_unexpired(client, make_company, make_student, make_job, auth_headers):
    _, company = make_company()
    student_user, _ = make_student()
    make_job(company, title="Hiển thị")
    make_job(company, title="Hạn là hôm nay", deadline=today())
    make_job(company, title="Quá hạn", deadline=today() - timedelta(days=1))
    for status in (
        JobStatus.DRAFT,
        JobStatus.PENDING_APPROVAL,
        JobStatus.REJECTED,
        JobStatus.CLOSED,
        JobStatus.EXPIRED,
    ):
        make_job(company, title=f"Ẩn {status.value}", status=status)

    response = client.get(JOBS, headers=auth_headers(student_user))
    assert response.status_code == 200
    body = response.json()
    assert {item["title"] for item in body["items"]} == {"Hiển thị", "Hạn là hôm nay"}
    assert {"items", "total", "page", "size", "pages"} <= set(body)


def test_term_job_hidden_from_students_outside_term(
    client, db, make_company, make_student, make_term, make_job, auth_headers
):
    _, company = make_company()
    term = make_term()
    member_user, _ = make_student(term=term)
    outsider_user, _ = make_student()
    term_job = make_job(company, title="Tin thuộc đợt", term_id=term.id)
    make_job(company, title="Tin tự do")

    def titles(user, **params):
        response = client.get(JOBS, params=params, headers=auth_headers(user))
        assert response.status_code == 200
        return {item["title"] for item in response.json()["items"]}

    assert titles(member_user) == {"Tin thuộc đợt", "Tin tự do"}
    assert titles(outsider_user) == {"Tin tự do"}
    assert titles(member_user, flow="term") == {"Tin thuộc đợt"}
    assert titles(outsider_user, flow="term") == set()
    assert titles(member_user, flow="free") == {"Tin tự do"}

    # Xem chi tiết: sinh viên ngoài đợt nhận 404 và không bị ghi lượt xem
    assert client.get(f"{JOBS}/{term_job.id}", headers=auth_headers(outsider_user)).status_code == 404
    assert client.get(f"{JOBS}/{term_job.id}", headers=auth_headers(member_user)).status_code == 200
    db.refresh(term_job)
    assert term_job.view_count == 1


def test_search_filters(client, catalog, make_company, make_student, make_job, auth_headers):
    _, company = make_company()
    student_user, _ = make_student()
    make_job(
        company,
        title="Backend Python",
        position="Backend Developer",
        location="Hà Nội",
        work_mode=WorkMode.REMOTE,
        salary_min=5_000_000,
        salary_max=10_000_000,
        skills=[(catalog.python.id, True)],
        major_ids=[catalog.se.id],
    )
    make_job(
        company,
        title="Frontend React",
        position="Frontend Developer",
        location="TP.HCM",
        work_mode=WorkMode.ONSITE,
        salary_min=15_000_000,
        salary_max=20_000_000,
        skills=[(catalog.react.id, True)],
        major_ids=[catalog.info.id],
    )
    make_job(
        company,
        title="Kiểm thử",
        position="QA",
        location="Hà Nội",
        work_mode=WorkMode.HYBRID,
        job_type_id=catalog.full_time.id,
    )

    def titles(**params):
        response = client.get(JOBS, params=params, headers=auth_headers(student_user))
        assert response.status_code == 200
        return {item["title"] for item in response.json()["items"]}

    assert titles(q="python") == {"Backend Python"}
    assert titles(position="qa") == {"Kiểm thử"}
    assert titles(location="Hà Nội") == {"Backend Python", "Kiểm thử"}
    assert titles(work_mode="REMOTE") == {"Backend Python"}
    assert titles(job_type_id=catalog.full_time.id) == {"Kiểm thử"}
    assert titles(skill_ids=[catalog.python.id]) == {"Backend Python"}
    assert titles(skill_ids=[catalog.python.id, catalog.react.id]) == {"Backend Python", "Frontend React"}
    # Tin không giới hạn ngành (Kiểm thử) hiện với mọi ngành
    assert titles(major_id=catalog.se.id) == {"Backend Python", "Kiểm thử"}
    assert titles(major_id=catalog.info.id) == {"Frontend React", "Kiểm thử"}
    assert titles(salary_from=12_000_000) == {"Frontend React"}
    assert titles(salary_to=8_000_000) == {"Backend Python"}
    assert titles(location="Hà Nội", work_mode="HYBRID") == {"Kiểm thử"}


def test_search_requires_student_role(client, make_company, auth_headers):
    company_user, _ = make_company()
    assert client.get(JOBS, headers=auth_headers(company_user)).status_code == 403
    assert client.get(JOBS).status_code == 401


# ---------------------------------------------------------------- Chi tiết và lượt xem
def test_student_view_is_recorded(client, db, make_company, make_student, make_job, auth_headers):
    _, company = make_company()
    student_user, _ = make_student()
    job = make_job(company)
    headers = auth_headers(student_user)

    first = client.get(f"{JOBS}/{job.id}", headers=headers)
    assert first.status_code == 200
    assert first.json()["view_count"] == 1
    assert client.get(f"{JOBS}/{job.id}", headers=headers).json()["view_count"] == 2
    assert db.scalar(select(func.count()).select_from(JobView).where(JobView.job_id == job.id)) == 2


def test_job_detail_visibility_by_role(client, db, make_company, make_student, make_job, make_user, auth_headers):
    owner_user, company = make_company()
    student_user, _ = make_student()
    draft = make_job(company, status=JobStatus.DRAFT)

    # Sinh viên không thấy tin nháp
    assert client.get(f"{JOBS}/{draft.id}", headers=auth_headers(student_user)).status_code == 404
    # Chủ tin xem được mọi trạng thái và không tính lượt xem
    assert client.get(f"{JOBS}/{draft.id}", headers=auth_headers(owner_user)).status_code == 200
    # Admin xem được mọi tin
    admin = make_user(UserRole.ADMIN)
    assert client.get(f"{JOBS}/{draft.id}", headers=auth_headers(admin)).status_code == 200
    assert db.scalar(select(func.count()).select_from(JobView)) == 0
    assert client.get(f"{JOBS}/9999", headers=auth_headers(admin)).status_code == 404


# ---------------------------------------------------------------- Tin của doanh nghiệp và thống kê
def test_my_jobs_lists_all_statuses_with_counts(
    client, make_company, make_student, make_job, make_application, auth_headers
):
    user, company = make_company()
    _, other_company = make_company()
    approved = make_job(company, title="Đã duyệt")
    make_job(company, title="Nháp", status=JobStatus.DRAFT)
    make_job(other_company, title="Của công ty khác")
    for _ in range(2):
        _, student = make_student()
        make_application(student, approved)
    headers = auth_headers(user)

    response = client.get(f"{JOBS}/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    by_title = {item["title"]: item for item in body["items"]}
    assert set(by_title) == {"Đã duyệt", "Nháp"}
    assert by_title["Đã duyệt"]["application_count"] == 2
    assert by_title["Nháp"]["application_count"] == 0

    drafts = client.get(f"{JOBS}/me", params={"status": "DRAFT"}, headers=headers).json()
    assert [item["title"] for item in drafts["items"]] == ["Nháp"]


def test_my_jobs_requires_company_role(client, make_student, auth_headers):
    student_user, _ = make_student()
    assert client.get(f"{JOBS}/me", headers=auth_headers(student_user)).status_code == 403


def test_job_stats(client, db, make_company, make_student, make_job, make_application, auth_headers):
    user, company = make_company()
    job = make_job(company, view_count=4)
    now = utcnow()
    for viewed_at in (now, now, now - timedelta(days=1), now - timedelta(days=40)):
        db.add(JobView(job_id=job.id, viewed_at=viewed_at))
    db.commit()
    _, student_a = make_student()
    _, student_b = make_student()
    make_application(student_a, job, ApplicationStatus.APPLIED)
    make_application(student_b, job, ApplicationStatus.HIRED)

    response = client.get(f"{JOBS}/{job.id}/stats", headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()
    assert body["total_views"] == 4
    assert body["total_applications"] == 2
    # Lượt xem cách đây 40 ngày nằm ngoài khoảng 30 ngày mặc định
    assert {item["day"]: item["views"] for item in body["views_by_day"]} == {
        str(now.date()): 2,
        str((now - timedelta(days=1)).date()): 1,
    }
    assert body["applications_by_status"]["APPLIED"] == 1
    assert body["applications_by_status"]["HIRED"] == 1
    assert body["applications_by_status"]["REJECTED"] == 0


# ---------------------------------------------------------------- Hàm dùng cho module khác / job định kỳ
def test_expire_overdue_jobs(db, make_company, make_job):
    _, company = make_company()
    overdue = make_job(company, deadline=today() - timedelta(days=1))
    due_today = make_job(company, deadline=today())
    future = make_job(company)
    draft = make_job(company, status=JobStatus.DRAFT, deadline=today() - timedelta(days=5))
    pending = make_job(company, status=JobStatus.PENDING_APPROVAL, deadline=today() - timedelta(days=5))

    assert job_service.expire_overdue_jobs(db) == 1

    for job in (overdue, due_today, future, draft, pending):
        db.refresh(job)
    assert overdue.status == JobStatus.EXPIRED
    assert due_today.status == JobStatus.APPROVED
    assert future.status == JobStatus.APPROVED
    assert draft.status == JobStatus.DRAFT
    assert pending.status == JobStatus.PENDING_APPROVAL
    assert job_service.expire_overdue_jobs(db) == 0


def test_list_jobs_by_term(db, make_company, make_term, make_job):
    _, company = make_company()
    term = make_term()
    make_job(company, term_id=term.id)
    make_job(company, term_id=term.id, status=JobStatus.DRAFT)
    make_job(company)

    page = job_service.list_jobs_by_term(db, term.id, PageParams(page=1, size=20))
    assert page["total"] == 2
    params = PageParams(page=1, size=20)
    approved_only = job_service.list_jobs_by_term(db, term.id, params, status=JobStatus.APPROVED)
    assert approved_only["total"] == 1
