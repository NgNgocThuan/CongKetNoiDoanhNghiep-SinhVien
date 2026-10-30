"""Test toàn diện phân hệ Quản lý tài khoản (Users). Người phụ trách: TV1."""
from app.core.enums import CompanySize, EmailStatus, UserRole, UserStatus, VerificationStatus
from app.models import Company, EmailLog, Faculty
from app.services.email_service import _email_body_cache


def test_list_users(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN, email="admin_user_list@test.com")
    make_user(UserRole.STUDENT, UserStatus.ACTIVE, email="student_1@test.com")
    make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL, email="company_1@test.com")

    headers = auth_headers(admin)

    # Lấy danh sách tất cả
    res = client.get("/api/v1/admin/users", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 3

    # Lọc theo role
    res_student = client.get("/api/v1/admin/users?role=STUDENT", headers=headers)
    assert res_student.status_code == 200
    assert all(item["role"] == "STUDENT" for item in res_student.json()["items"])

    # Lọc theo status
    res_status = client.get("/api/v1/admin/users?status=PENDING_APPROVAL", headers=headers)
    assert res_status.status_code == 200
    assert all(item["status"] == "PENDING_APPROVAL" for item in res_status.json()["items"])

    # Tìm kiếm theo q
    res_q = client.get("/api/v1/admin/users?q=student_1", headers=headers)
    assert res_q.status_code == 200
    assert len(res_q.json()["items"]) >= 1


def test_list_users_forbidden_for_non_admin(client, make_user, auth_headers):
    student = make_user(UserRole.STUDENT)
    res = client.get("/api/v1/admin/users", headers=auth_headers(student))
    assert res.status_code == 403


def test_get_user_detail(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    target = make_user(UserRole.STUDENT, email="detail_target@test.com")

    headers = auth_headers(admin)
    res = client.get(f"/api/v1/admin/users/{target.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "detail_target@test.com"

    # User không tồn tại -> 404
    res_404 = client.get("/api/v1/admin/users/99999", headers=headers)
    assert res_404.status_code == 404


def test_lock_and_unlock_user(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN, email="admin_locker@test.com")
    student = make_user(UserRole.STUDENT, UserStatus.ACTIVE, email="student_to_lock@test.com")
    headers = auth_headers(admin)

    # 1. Khóa tài khoản thành công
    res_lock = client.post(
        f"/api/v1/admin/users/{student.id}/lock",
        json={"reason": "Vi phạm quy chế sử dụng hệ thống"},
        headers=headers,
    )
    assert res_lock.status_code == 200
    locked_body = res_lock.json()
    assert locked_body["status"] == UserStatus.LOCKED.value
    assert locked_body["locked_reason"] == "Vi phạm quy chế sử dụng hệ thống"

    # 2. Khóa lại user đã bị khóa -> 409 Conflict
    res_relock = client.post(
        f"/api/v1/admin/users/{student.id}/lock",
        json={"reason": "Khóa lần 2"},
        headers=headers,
    )
    assert res_relock.status_code == 409

    # 3. Tự khóa chính mình -> 400 Bad Request
    res_self_lock = client.post(
        f"/api/v1/admin/users/{admin.id}/lock",
        json={"reason": "Tự khóa"},
        headers=headers,
    )
    assert res_self_lock.status_code == 400

    # 4. Mở khóa tài khoản sinh viên -> về ACTIVE
    res_unlock = client.post(
        f"/api/v1/admin/users/{student.id}/unlock",
        headers=headers,
    )
    assert res_unlock.status_code == 200
    assert res_unlock.json()["status"] == UserStatus.ACTIVE.value
    assert res_unlock.json()["locked_reason"] is None

    # 5. Mở khóa user chưa bị khóa -> 400
    res_unlock_active = client.post(
        f"/api/v1/admin/users/{student.id}/unlock",
        headers=headers,
    )
    assert res_unlock_active.status_code == 400

    # 6. Khóa và mở khóa tài khoản doanh nghiệp CHƯA được duyệt -> về PENDING_APPROVAL
    company_user = make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL, email="comp_pending@test.com")
    comp = Company(
        user_id=company_user.id,
        name="Công ty Chờ Duyệt",
        tax_code="0987654321",
        company_size=CompanySize.S_11_50,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(comp)
    db.commit()

    client.post(f"/api/v1/admin/users/{company_user.id}/lock", json={"reason": "Tạm dừng"}, headers=headers)
    res_comp_unlock = client.post(f"/api/v1/admin/users/{company_user.id}/unlock", headers=headers)
    assert res_comp_unlock.status_code == 200
    assert res_comp_unlock.json()["status"] == UserStatus.PENDING_APPROVAL.value


def test_create_admin(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    faculty = Faculty(code="CNTT_ADM", name="Khoa CNTT Admin Test")
    db.add(faculty)
    db.commit()

    headers = auth_headers(admin)
    data = {
        "email": "new_admin@school.edu.vn",
        "password": "AdminPassword@123",
        "full_name": "Nguyen Van Quan Tri",
        "faculty_id": faculty.id,
        "position": "Chuyên viên QTKD",
        "phone": "0988776655",
    }
    # Tạo admin mới thành công
    res = client.post("/api/v1/admin/users/admins", json=data, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "new_admin@school.edu.vn"
    assert body["role"] == UserRole.ADMIN.value
    assert body["admin"]["full_name"] == "Nguyen Van Quan Tri"

    # Trùng email -> 409
    res_dup = client.post("/api/v1/admin/users/admins", json=data, headers=headers)
    assert res_dup.status_code == 409

    # Sai faculty_id -> 404
    bad_faculty_data = {**data, "email": "admin2@school.edu.vn", "faculty_id": 99999}
    res_bad_fac = client.post("/api/v1/admin/users/admins", json=bad_faculty_data, headers=headers)
    assert res_bad_fac.status_code == 404


def test_create_admin_with_inactive_faculty_404(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    inactive_faculty = Faculty(code="INACTIVE_FAC", name="Khoa Ngưng Hoạt Động", is_active=False)
    db.add(inactive_faculty)
    db.commit()

    headers = auth_headers(admin)
    data = {
        "email": "admin_inactive_fac@school.edu.vn",
        "password": "AdminPassword@123",
        "full_name": "Nguyen Van Quan Tri 2",
        "faculty_id": inactive_faculty.id,
    }
    res = client.post("/api/v1/admin/users/admins", json=data, headers=headers)
    assert res.status_code == 404
    assert "Không tìm thấy khoa" in res.json()["error"]["message"]


def test_unlock_company_without_company_profile(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    headers = auth_headers(admin)

    comp_user_no_profile = make_user(UserRole.COMPANY, UserStatus.LOCKED, email="comp_no_prof@test.com")
    res_unlock = client.post(f"/api/v1/admin/users/{comp_user_no_profile.id}/unlock", headers=headers)
    assert res_unlock.status_code == 200
    assert res_unlock.json()["status"] == UserStatus.PENDING_APPROVAL.value



def test_admin_list_email_logs(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN, email="admin_emails@test.com")
    headers = auth_headers(admin)

    log1 = EmailLog(
        recipient_email="student@univ.edu.vn",
        type="PASSWORD_RESET",
        subject="Đặt lại mật khẩu",
        status=EmailStatus.SENT,
    )
    log2 = EmailLog(
        recipient_email="hr@corp.com",
        type="COMPANY_APPROVED",
        subject="Duyệt tài khoản",
        status=EmailStatus.PENDING,
    )
    db.add_all([log1, log2])
    db.commit()

    # Admin xem danh sách thành công
    res = client.get("/api/v1/admin/users/email-logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert any(item["recipient_email"] == "student@univ.edu.vn" for item in data["items"])

    # Lọc theo status
    res_filter = client.get("/api/v1/admin/users/email-logs?status=SENT", headers=headers)
    assert res_filter.status_code == 200
    assert all(item["status"] == "SENT" for item in res_filter.json()["items"])

    # Non-admin bị 403
    student = make_user(UserRole.STUDENT, email="student_peek@test.com")
    res_forbidden = client.get("/api/v1/admin/users/email-logs", headers=auth_headers(student))
    assert res_forbidden.status_code == 403


def test_admin_retry_failed_emails(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN, email="admin_retry@test.com")
    headers = auth_headers(admin)

    failed_log = EmailLog(
        recipient_email="failed_user@test.com",
        type="ACCOUNT_LOCKED",
        subject="Khóa tài khoản",
        status=EmailStatus.FAILED,
        retry_count=0,
    )
    db.add(failed_log)
    db.commit()
    db.refresh(failed_log)

    # Lưu nội dung vào cache
    _email_body_cache[failed_log.id] = "<h1>Tài khoản bị khóa</h1>"

    # Gọi API retry
    res = client.post("/api/v1/admin/users/email-logs/retry", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["retried_count"] >= 1

    # Kiểm tra log đã chuyển sang PENDING
    db.refresh(failed_log)
    assert failed_log.status in (EmailStatus.PENDING, EmailStatus.SENT)
