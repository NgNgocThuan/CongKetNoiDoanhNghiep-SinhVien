"""Test quản lý sinh viên (nhà trường): danh sách, chi tiết, sửa, import Excel/CSV, cấp tài khoản, thành tích, chứng chỉ."""
import io

import pytest
from openpyxl import Workbook
from sqlalchemy import select

from app.core.enums import CertificateSource, UserRole, UserStatus
from app.models import (
    EmailLog,
    Faculty,
    Major,
    PasswordResetToken,
    Student,
    StudentCertificate,
    StudentProfile,
    User,
)

URL = "/api/v1/admin/students"


@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    """Tác vụ nền gửi email mở session riêng (MariaDB thật): thay bằng hàm rỗng, email_logs vẫn được ghi."""
    monkeypatch.setattr("app.services.email_service.send_email_task", lambda *args, **kwargs: None)


HEADER = "student_code,full_name,email,date_of_birth,class_name,faculty,major,cohort,gpa,phone\n"


def _school(db):
    faculty = Faculty(code="CNTT", name="Công nghệ thông tin")
    db.add(faculty)
    db.flush()
    major = Major(faculty_id=faculty.id, code="KTPM", name="Kỹ thuật phần mềm")
    other_faculty = Faculty(code="KT", name="Kinh tế")
    db.add_all([major, other_faculty])
    db.commit()
    return faculty, major


def _csv(rows: str, header: str = HEADER):
    return {"file": ("students.csv", (header + rows).encode("utf-8"), "text/csv")}


def _admin(make_user, auth_headers):
    return auth_headers(make_user(UserRole.ADMIN))


def _make_student(db, make_user, faculty, major, code="SV001"):
    user = make_user(UserRole.STUDENT)
    student = Student(
        user_id=user.id, student_code=code, full_name="Nguyễn Văn A", faculty_id=faculty.id, major_id=major.id, cohort="K65"
    )
    db.add(student)
    db.flush()
    db.add(StudentProfile(student_id=student.id))
    db.commit()
    return student


# ---------------------------------------------------------------- Import
def test_import_creates_students_and_reports_row_errors(client, db, make_user, auth_headers):
    _school(db)
    headers = _admin(make_user, auth_headers)
    rows = (
        "SV001,Nguyễn Văn A,a@school.vn,01/05/2003,K65A,CNTT,KTPM,K65,3.2,0900000001\n"  # ok
        "SV002,Trần Thị B,b@school.vn,2003-06-02,K65A,Công nghệ thông tin,Kỹ thuật phần mềm,K65,3.5,\n"  # ok (theo tên)
        "SV003,Lê C,c@school.vn,,,CNTT,KTPM,K65,5.0,\n"  # GPA sai
        "SV004,Phạm D,a@school.vn,,,CNTT,KTPM,K65,3.0,\n"  # trùng email với SV001
        "SV005,Hoàng E,e@school.vn,,,XXX,KTPM,K65,3.0,\n"  # khoa không tồn tại
        "SV006,Vũ F,f@school.vn,,,KT,KTPM,K65,3.0,\n"  # ngành không thuộc khoa KT
        ",Không mã,g@school.vn,,,CNTT,KTPM,K65,3.0,\n"  # thiếu mã
        "SV008,Đỗ H,khong-hop-le,,,CNTT,KTPM,K65,3.0,\n"  # email sai
        "SV009,Ngô I,i@school.vn,31/02/2003,,CNTT,KTPM,K65,3.0,\n"  # ngày sai
    )
    response = client.post(f"{URL}/import", files=_csv(rows), headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    batch = body["batch"]
    assert (batch["total_rows"], batch["success_rows"], batch["failed_rows"]) == (9, 2, 7)
    assert body["activation_emails_queued"] == 2
    assert {e["row"] for e in batch["errors"]} == {4, 5, 6, 7, 8, 9, 10}  # số dòng tính cả dòng tiêu đề
    by_row = {e["row"]: e for e in batch["errors"]}
    assert "GPA" in by_row[4]["message"]
    assert "Email" in by_row[5]["message"]
    assert by_row[8]["key"] is None

    # Chỉ 2 sinh viên đúng được lưu, ở trạng thái chờ kích hoạt, có hồ sơ + email kích hoạt + token
    assert db.scalars(select(Student.student_code).order_by(Student.student_code)).all() == ["SV001", "SV002"]
    sv1 = db.scalar(select(Student).where(Student.student_code == "SV001"))
    assert sv1.user.status == UserStatus.PENDING_ACTIVATION and sv1.user.password_hash is None
    assert sv1.profile is not None and sv1.import_batch_id == batch["id"]
    assert str(sv1.gpa) == "3.20" and str(sv1.date_of_birth) == "2003-05-01"
    assert len(db.scalars(select(EmailLog).where(EmailLog.type == "ACCOUNT_ACTIVATION")).all()) == 2
    assert len(db.scalars(select(PasswordResetToken)).all()) == 2

    # Lịch sử import có dòng lỗi
    detail = client.get(f"{URL}/imports/{batch['id']}", headers=headers).json()
    assert detail["failed_rows"] == 7 and len(detail["errors"]) == 7
    history = client.get(f"{URL}/imports", headers=headers).json()
    assert history["total"] == 1 and "errors" not in history["items"][0]


def test_import_upserts_by_student_code(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    headers = _admin(make_user, auth_headers)
    client.post(f"{URL}/import", files=_csv("SV001,Nguyễn Văn A,a@school.vn,,,CNTT,KTPM,K65,3.0,\n"), headers=headers)

    # Import lại: đổi GPA và tên; ô trống giữ nguyên dữ liệu cũ; không gửi lại email
    again = client.post(
        f"{URL}/import", files=_csv("SV001,Nguyễn Văn An,,,,,,,3.8,\n"), headers=headers
    ).json()
    assert again["batch"]["success_rows"] == 1 and again["activation_emails_queued"] == 0
    student = db.scalar(select(Student).where(Student.student_code == "SV001"))
    db.refresh(student)
    assert student.full_name == "Nguyễn Văn An" and str(student.gpa) == "3.80" and student.cohort == "K65"
    assert db.scalar(select(Student.id).where(Student.student_code == "SV002")) is None
    assert len(db.scalars(select(User).where(User.role == UserRole.STUDENT)).all()) == 1


def test_import_excel_with_vietnamese_headers(client, db, make_user, auth_headers):
    _school(db)
    headers = _admin(make_user, auth_headers)
    wb = Workbook()
    ws = wb.active
    ws.append(["Mã sinh viên", "Họ và tên", "Email", "Ngày sinh", "Lớp", "Khoa", "Ngành", "Khóa học", "GPA"])
    ws.append(["SV100", "Nguyễn Văn X", "x@school.vn", "01/02/2003", "K65A", "CNTT", "KTPM", "K65", "3,45"])
    buffer = io.BytesIO()
    wb.save(buffer)
    files = {"file": ("sv.xlsx", buffer.getvalue(), "application/octet-stream")}
    body = client.post(f"{URL}/import", files=files, headers=headers).json()
    assert body["batch"]["success_rows"] == 1, body
    student = db.scalar(select(Student).where(Student.student_code == "SV100"))
    assert str(student.gpa) == "3.45"


def test_import_rejects_bad_files(client, db, make_user, auth_headers):
    _school(db)
    headers = _admin(make_user, auth_headers)
    missing_col = client.post(f"{URL}/import", files=_csv("SV1,A\n", header="student_code,full_name\n"), headers=headers)
    assert missing_col.status_code == 400 and "email" in missing_col.json()["error"]["message"]
    wrong_ext = client.post(f"{URL}/import", files={"file": ("a.txt", b"x", "text/plain")}, headers=headers)
    assert wrong_ext.status_code == 400
    empty = client.post(f"{URL}/import", files=_csv(""), headers=headers)
    assert empty.status_code == 400


def test_import_requires_admin(client, make_user, auth_headers):
    student = auth_headers(make_user(UserRole.STUDENT))
    assert client.post(f"{URL}/import", files=_csv(""), headers=student).status_code == 403
    assert client.get(URL, headers=student).status_code == 403


# ---------------------------------------------------------------- Danh sách / chi tiết / sửa
def test_list_filter_detail_and_update(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    headers = _admin(make_user, auth_headers)
    student = _make_student(db, make_user, faculty, major)
    _make_student(db, make_user, faculty, major, code="SV002").cohort = "K66"
    db.commit()

    assert client.get(URL, headers=headers).json()["total"] == 2
    assert client.get(URL, params={"cohort": "K66"}, headers=headers).json()["items"][0]["student_code"] == "SV002"
    assert client.get(URL, params={"q": "sv001"}, headers=headers).json()["total"] == 1
    assert client.get(URL, params={"faculty_id": 999}, headers=headers).json()["total"] == 0

    detail = client.get(f"{URL}/{student.id}", headers=headers).json()
    assert detail["official"]["academic"]["faculty_name"] == "Công nghệ thông tin"
    assert detail["self_declared"]["profile"]["is_open_to_work"] is False
    assert client.get(f"{URL}/999", headers=headers).status_code == 404

    updated = client.put(f"{URL}/{student.id}", json={"gpa": "3.75", "class_name": "K65B"}, headers=headers)
    assert updated.status_code == 200 and updated.json()["gpa"] == "3.75"
    assert client.put(f"{URL}/{student.id}", json={"gpa": "4.5"}, headers=headers).status_code == 422
    other_faculty = db.scalar(select(Faculty).where(Faculty.code == "KT"))
    # Đổi sang khoa khác mà ngành cũ không thuộc khoa đó
    bad = client.put(f"{URL}/{student.id}", json={"faculty_id": other_faculty.id}, headers=headers)
    assert bad.status_code == 400


# ---------------------------------------------------------------- Cấp tài khoản
def test_issue_account_only_for_pending(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    headers = _admin(make_user, auth_headers)
    student = _make_student(db, make_user, faculty, major)  # user ACTIVE
    assert client.post(f"{URL}/{student.id}/issue-account", headers=headers).status_code == 409

    student.user.status = UserStatus.PENDING_ACTIVATION
    db.commit()
    assert client.post(f"{URL}/{student.id}/issue-account", headers=headers).status_code == 200
    assert client.post(f"{URL}/{student.id}/issue-account", headers=headers).status_code == 200
    # Gửi lại thì token cũ bị thu hồi: chỉ còn một token chưa dùng
    assert len(db.scalars(select(PasswordResetToken)).all()) == 1


# ---------------------------------------------------------------- Thành tích / chứng chỉ
def test_achievements_and_certificate_verification(client, db, make_user, auth_headers):
    faculty, major = _school(db)
    headers = _admin(make_user, auth_headers)
    student = _make_student(db, make_user, faculty, major)

    created = client.post(
        f"{URL}/{student.id}/achievements", json={"type": "RESEARCH", "title": "Đề tài NCKH cấp trường"}, headers=headers
    )
    assert created.status_code == 201 and created.json()["type"] == "RESEARCH"
    aid = created.json()["id"]
    assert client.delete(f"{URL}/{student.id}/achievements/{aid}", headers=headers).status_code == 204
    assert client.delete(f"{URL}/{student.id}/achievements/{aid}", headers=headers).status_code == 404

    cert = StudentCertificate(student_id=student.id, name="IELTS 7.0", source=CertificateSource.SELF)
    db.add(cert)
    db.commit()
    verified = client.post(f"{URL}/certificates/{cert.id}/verify", headers=headers)
    assert verified.status_code == 200
    assert verified.json()["is_verified"] is True and verified.json()["verified_at"] is not None
    assert client.post(f"{URL}/certificates/999/verify", headers=headers).status_code == 404


def test_sync_not_supported(client, make_user, auth_headers):
    headers = _admin(make_user, auth_headers)
    response = client.post(f"{URL}/sync", headers=headers)
    assert response.status_code == 501 and response.json()["error"]["code"] == "NOT_IMPLEMENTED"
