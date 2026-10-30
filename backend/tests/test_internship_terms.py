"""Test đợt thực tập: tạo/sửa, chuyển trạng thái, sinh viên trong đợt, import, phân công giảng viên, kết quả thực tập."""
from datetime import date

from sqlalchemy import select

from app.core.enums import ApplicationStatus, JobStatus, UserRole
from app.models import (
    Application,
    Company,
    Faculty,
    InternshipResult,
    Job,
    JobType,
    Lecturer,
    Major,
    Notification,
    Student,
    StudentProfile,
)
from app.services import internship_service

URL = "/api/v1/internship-terms"
TERM = {
    "name": "Thực tập HK1",
    "semester": "HK1",
    "academic_year": "2025-2026",
    "start_date": "2025-09-01",
    "end_date": "2026-01-15",
}


def _admin(make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    return admin, auth_headers(admin)


def _school(db):
    faculty = Faculty(code="CNTT", name="Công nghệ thông tin")
    db.add(faculty)
    db.flush()
    major = Major(faculty_id=faculty.id, code="KTPM", name="Kỹ thuật phần mềm")
    db.add(major)
    db.commit()
    return faculty, major


def _student(db, make_user, faculty, major, code):
    user = make_user(UserRole.STUDENT)
    student = Student(
        user_id=user.id, student_code=code, full_name=f"SV {code}", faculty_id=faculty.id, major_id=major.id, cohort="K65"
    )
    db.add(student)
    db.flush()
    db.add(StudentProfile(student_id=student.id))
    db.commit()
    return user, student


def _create_term(client, headers, **overrides):
    return client.post(URL, json={**TERM, **overrides}, headers=headers)


def _advance(client, headers, term_id, *statuses):
    for status in statuses:
        assert client.post(f"{URL}/{term_id}/status", json={"status": status}, headers=headers).status_code == 200


def _company_with_hire(db, make_user, student, term_id, status=ApplicationStatus.HIRED):
    """Tạo công ty + tin thuộc đợt + đơn của sinh viên với trạng thái cho trước."""
    user = make_user(UserRole.COMPANY)
    company = Company(user_id=user.id, name="ACME", tax_code=f"TAX{user.id}")
    job_type = JobType(code=f"JT{user.id}", name="Thực tập")
    db.add_all([company, job_type])
    db.flush()
    job = Job(
        company_id=company.id,
        term_id=term_id,
        title="Intern",
        position="Dev",
        job_type_id=job_type.id,
        description="mô tả",
        deadline=date(2030, 1, 1),
        status=JobStatus.APPROVED,
    )
    db.add(job)
    db.flush()
    db.add(Application(student_id=student.id, job_id=job.id, cv_id=1, current_status=status))
    db.commit()
    return user, company, job


# ---------------------------------------------------------------- Đợt
def test_term_create_validate_and_status_flow(client, make_user, auth_headers):
    _, headers = _admin(make_user, auth_headers)
    created = _create_term(client, headers)
    assert created.status_code == 201
    term = created.json()
    assert term["status"] == "DRAFT" and term["student_count"] == 0

    assert _create_term(client, headers, start_date="2026-02-01").status_code == 422  # bắt đầu sau kết thúc
    assert client.put(f"{URL}/{term['id']}", json={"start_date": "2027-01-01"}, headers=headers).status_code == 400
    assert client.put(f"{URL}/{term['id']}", json={"name": "Tên mới"}, headers=headers).json()["name"] == "Tên mới"

    skip = client.post(f"{URL}/{term['id']}/status", json={"status": "ONGOING"}, headers=headers)
    assert skip.status_code == 400  # không được nhảy cóc
    _advance(client, headers, term["id"], "OPEN", "ONGOING", "CLOSED")
    assert client.post(f"{URL}/{term['id']}/status", json={"status": "OPEN"}, headers=headers).status_code == 400
    assert client.put(f"{URL}/{term['id']}", json={"name": "X"}, headers=headers).status_code == 409  # đợt đã đóng


def test_term_list_filters_and_permissions(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    _, headers = _admin(make_user, auth_headers)
    t1 = _create_term(client, headers).json()
    t2 = _create_term(client, headers, name="HK2", semester="HK2", academic_year="2026-2027").json()

    assert client.get(URL, params={"academic_year": "2026-2027"}, headers=headers).json()["total"] == 1
    assert client.get(URL, params={"status": "OPEN"}, headers=headers).json()["total"] == 0

    user, student = _student(db, make_user, faculty, major, "SV001")
    other_user, _ = _student(db, make_user, faculty, major, "SV002")
    client.post(f"{URL}/{t1['id']}/students", json={"student_ids": [student.id]}, headers=headers)

    mine = client.get(URL, headers=auth_headers(user)).json()
    assert [t["id"] for t in mine["items"]] == [t1["id"]]
    assert client.get(URL, headers=auth_headers(other_user)).json()["total"] == 0
    assert client.get(f"{URL}/{t1['id']}", headers=auth_headers(user)).status_code == 200
    assert client.get(f"{URL}/{t2['id']}", headers=auth_headers(user)).status_code == 403
    assert client.get(f"{URL}/999", headers=headers).status_code == 404

    assert client.post(URL, json=TERM, headers=auth_headers(user)).status_code == 403
    company = make_user(UserRole.COMPANY)
    assert client.get(URL, headers=auth_headers(company)).status_code == 403


# ---------------------------------------------------------------- Sinh viên trong đợt
def test_add_remove_students_and_is_student_in_term(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    _, headers = _admin(make_user, auth_headers)
    term_id = _create_term(client, headers).json()["id"]
    s1 = _student(db, make_user, faculty, major, "SV001")[1]
    s2 = _student(db, make_user, faculty, major, "SV002")[1]

    first = client.post(f"{URL}/{term_id}/students", json={"student_ids": [s1.id, s1.id, 999]}, headers=headers)
    assert first.status_code == 201
    assert first.json() == {"added": 1, "already_in_term": 0, "not_found_ids": [999]}
    again = client.post(f"{URL}/{term_id}/students", json={"student_ids": [s1.id, s2.id]}, headers=headers).json()
    assert again["added"] == 1 and again["already_in_term"] == 1

    assert internship_service.is_student_in_term(db, s1.id, term_id) is True
    assert internship_service.is_student_in_term(db, s1.id, term_id + 1) is False
    # Mỗi sinh viên có một kết quả PENDING và được thông báo
    assert len(db.scalars(select(InternshipResult)).all()) == 2
    assert len(db.scalars(select(Notification).where(Notification.user_id == s1.user_id)).all()) == 1

    listing = client.get(f"{URL}/{term_id}/students", headers=headers).json()
    assert listing["total"] == 2 and listing["items"][0]["student_code"] == "SV001"
    assert client.get(f"{URL}/{term_id}", headers=headers).json()["student_count"] == 2

    assert client.delete(f"{URL}/{term_id}/students/{s2.id}", headers=headers).status_code == 204
    assert client.delete(f"{URL}/{term_id}/students/{s2.id}", headers=headers).status_code == 404
    assert internship_service.is_student_in_term(db, s2.id, term_id) is False

    _advance(client, headers, term_id, "OPEN", "ONGOING", "CLOSED")
    assert client.post(f"{URL}/{term_id}/students", json={"student_ids": [s2.id]}, headers=headers).status_code == 409


def test_import_term_students(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    _, headers = _admin(make_user, auth_headers)
    term_id = _create_term(client, headers).json()["id"]
    _student(db, make_user, faculty, major, "SV001")
    _student(db, make_user, faculty, major, "SV002")

    data = "student_code\nSV001\nSV002\nSV999\n\nSV001\n"  # SV999 không tồn tại, SV001 lặp lại
    files = {"file": ("term.csv", data.encode("utf-8"), "text/csv")}
    response = client.post(f"{URL}/{term_id}/students/import", files=files, headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["added"] == 2
    batch = body["batch"]
    assert (batch["total_rows"], batch["success_rows"], batch["failed_rows"]) == (4, 2, 2)
    assert {e["key"] for e in batch["errors"]} == {"SV999", "SV001"}

    bad = {"file": ("term.csv", b"ma\nSV001\n", "text/csv")}
    assert client.post(f"{URL}/{term_id}/students/import", files=bad, headers=headers).status_code == 400


def test_assign_lecturers_in_bulk(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    _, headers = _admin(make_user, auth_headers)
    term_id = _create_term(client, headers).json()["id"]
    s1 = _student(db, make_user, faculty, major, "SV001")[1]
    s2 = _student(db, make_user, faculty, major, "SV002")[1]
    outsider = _student(db, make_user, faculty, major, "SV003")[1]
    client.post(f"{URL}/{term_id}/students", json={"student_ids": [s1.id, s2.id]}, headers=headers)
    lecturer = Lecturer(code="GV1", full_name="Cô Lan", faculty_id=faculty.id)
    retired = Lecturer(code="GV2", full_name="Thầy cũ", faculty_id=faculty.id, is_active=False)
    db.add_all([lecturer, retired])
    db.commit()

    ok = client.post(
        f"{URL}/{term_id}/assign-lecturers",
        json={"lecturer_id": lecturer.id, "student_ids": [s1.id, s2.id, outsider.id]},
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json() == {"updated": 2, "not_in_term_ids": [outsider.id]}
    listing = client.get(f"{URL}/{term_id}/students", params={"lecturer_id": lecturer.id}, headers=headers).json()
    assert listing["total"] == 2 and listing["items"][0]["lecturer_name"] == "Cô Lan"

    assert client.post(
        f"{URL}/{term_id}/assign-lecturers", json={"lecturer_id": retired.id, "student_ids": [s1.id]}, headers=headers
    ).status_code == 400
    assert client.post(
        f"{URL}/{term_id}/assign-lecturers", json={"lecturer_id": 999, "student_ids": [s1.id]}, headers=headers
    ).status_code == 404
    cleared = client.post(
        f"{URL}/{term_id}/assign-lecturers", json={"lecturer_id": None, "student_ids": [s1.id]}, headers=headers
    )
    assert cleared.json()["updated"] == 1


def test_term_jobs_visibility(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    _, headers = _admin(make_user, auth_headers)
    term_id = _create_term(client, headers).json()["id"]
    user, student = _student(db, make_user, faculty, major, "SV001")
    outsider_user, _ = _student(db, make_user, faculty, major, "SV002")
    client.post(f"{URL}/{term_id}/students", json={"student_ids": [student.id]}, headers=headers)
    _, _, job = _company_with_hire(db, make_user, student, term_id)
    job.status = JobStatus.PENDING_APPROVAL
    db.commit()

    assert client.get(f"{URL}/{term_id}/jobs", headers=headers).json()["total"] == 1  # admin thấy cả tin chờ duyệt
    assert client.get(f"{URL}/{term_id}/jobs", headers=auth_headers(user)).json()["total"] == 0  # sinh viên chỉ thấy đã duyệt
    job.status = JobStatus.APPROVED
    db.commit()
    seen = client.get(f"{URL}/{term_id}/jobs", headers=auth_headers(user)).json()
    assert seen["total"] == 1 and seen["items"][0]["company_name"] == "ACME"
    assert client.get(f"{URL}/{term_id}/jobs", headers=auth_headers(outsider_user)).status_code == 403


# ---------------------------------------------------------------- Kết quả thực tập
def _setup_result(client, db, make_user, auth_headers, status=ApplicationStatus.HIRED):
    faculty, major = _school(db)
    _, headers = _admin(make_user, auth_headers)
    term_id = _create_term(client, headers).json()["id"]
    student_user, student = _student(db, make_user, faculty, major, "SV001")
    client.post(f"{URL}/{term_id}/students", json={"student_ids": [student.id]}, headers=headers)
    result_id = client.get(f"{URL}/{term_id}/results", headers=headers).json()["items"][0]["id"]
    company_user, company, _ = _company_with_hire(db, make_user, student, term_id, status)
    return headers, term_id, result_id, student_user, company_user, company


def test_company_evaluation_confirm_flow(client, db, make_user, auth_headers):
    headers, term_id, result_id, student_user, company_user, company = _setup_result(
        client, db, make_user, auth_headers
    )
    evaluation = {"evaluation": "Làm việc tốt", "score": "8.5"}
    url = f"{URL}/results/{result_id}"

    # Chưa đến thời điểm đánh giá: đợt còn DRAFT
    assert client.put(f"{url}/evaluation", json=evaluation, headers=auth_headers(company_user)).status_code == 400
    _advance(client, headers, term_id, "OPEN", "ONGOING")

    submitted = client.put(f"{url}/evaluation", json=evaluation, headers=auth_headers(company_user))
    assert submitted.status_code == 200, submitted.text
    body = submitted.json()
    assert body["company_id"] == company.id and float(body["company_score"]) == 8.5 and body["evaluated_at"]
    assert body["application_id"] is not None and body["result"] == "PENDING"
    # Nhà trường (admin) được thông báo
    assert len(db.scalars(select(Notification).where(Notification.type == "INTERNSHIP_EVALUATION")).all()) == 1

    assert client.put(f"{url}/evaluation", json={"evaluation": "x", "score": "11"}, headers=auth_headers(company_user)).status_code == 422

    review = client.put(f"{url}/lecturer-review", json={"comment": "Hoàn thành tốt", "score": "9"}, headers=headers)
    assert review.status_code == 200 and review.json()["lecturer_comment"] == "Hoàn thành tốt"
    assert client.put(f"{url}/lecturer-review", json={}, headers=headers).status_code == 422

    confirmed = client.post(f"{url}/confirm", json={"result": "PASSED"}, headers=headers)
    assert confirmed.status_code == 200
    assert confirmed.json()["result"] == "PASSED" and confirmed.json()["confirmed_at"]
    assert client.post(f"{url}/confirm", json={"result": "FAILED"}, headers=headers).status_code == 409
    assert client.put(f"{url}/evaluation", json=evaluation, headers=auth_headers(company_user)).status_code == 409
    assert client.post(f"{url}/confirm", json={"result": "PENDING"}, headers=headers).status_code == 422
    assert len(db.scalars(select(Notification).where(Notification.user_id == student_user.id,
                                                       Notification.type == "INTERNSHIP_RESULT")).all()) == 1

    by_status = client.get(f"{URL}/{term_id}/results", params={"result": "PASSED"}, headers=headers).json()
    assert by_status["total"] == 1 and by_status["items"][0]["student_code"] == "SV001"
    assert client.get(f"{URL}/{term_id}/results", params={"result": "FAILED"}, headers=headers).json()["total"] == 0


def test_only_hiring_company_can_evaluate(client, db, make_user, auth_headers):
    headers, term_id, result_id, student_user, company_user, _ = _setup_result(client, db, make_user, auth_headers)
    _advance(client, headers, term_id, "OPEN", "ONGOING")
    url = f"{URL}/results/{result_id}/evaluation"
    body = {"evaluation": "ok", "score": "7"}

    stranger = make_user(UserRole.COMPANY)
    db.add(Company(user_id=stranger.id, name="Khác", tax_code="TAX-X"))
    db.commit()
    assert client.put(url, json=body, headers=auth_headers(stranger)).status_code == 403  # công ty khác
    assert client.put(url, json=body, headers=auth_headers(student_user)).status_code == 403  # sai role
    assert client.put(url, json=body, headers=headers).status_code == 403  # admin cũng không gửi thay doanh nghiệp
    assert client.put(f"{URL}/results/999/evaluation", json=body, headers=auth_headers(company_user)).status_code == 404


def test_company_not_hiring_student_is_rejected(client, db, make_user, auth_headers):
    headers, term_id, result_id, _, company_user, _ = _setup_result(
        client, db, make_user, auth_headers, status=ApplicationStatus.OFFER
    )
    _advance(client, headers, term_id, "OPEN", "ONGOING")
    response = client.put(
        f"{URL}/results/{result_id}/evaluation", json={"evaluation": "ok", "score": "7"}, headers=auth_headers(company_user)
    )
    assert response.status_code == 403  # mới OFFER, chưa HIRED


def test_cannot_remove_student_with_confirmed_result(client, db, make_user, auth_headers):
    headers, term_id, result_id, _, _, _ = _setup_result(client, db, make_user, auth_headers)
    student_id = db.scalar(select(Student.id))
    client.post(f"{URL}/results/{result_id}/confirm", json={"result": "FAILED"}, headers=headers)
    assert client.delete(f"{URL}/{term_id}/students/{student_id}", headers=headers).status_code == 409
