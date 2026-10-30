"""Test toàn diện phân hệ Kiểm duyệt Doanh nghiệp. Người phụ trách: TV1."""
from app.core.enums import CompanyDocType, CompanySize, UserRole, UserStatus, VerificationStatus
from app.models import Company, CompanyDocument, Notification


def test_company_approval_e2e_flow(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN, email="admin_checker@school.edu.vn")
    admin_headers = auth_headers(admin)

    # 1. Doanh nghiệp tự đăng ký qua /auth/register-company
    reg_data = {
        "email": "hr@vinfast.vn",
        "password": "Password@123",
        "company_name": "VinFast Auto",
        "tax_code": "0108999888",
        "contact_name": "Pham Nhat V",
        "contact_phone": "0909000111",
    }
    reg_res = client.post("/api/v1/auth/register-company", json=reg_data)
    assert reg_res.status_code == 201
    company_id = reg_res.json()["company_id"]
    user_id = reg_res.json()["user_id"]

    # 2. Đăng nhập ngay lập tức -> Bị chặn vì chưa được trường duyệt
    blocked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@vinfast.vn", "password": "Password@123"},
    )
    assert blocked_login.status_code == 403
    assert blocked_login.json()["error"]["code"] == "ACCOUNT_PENDING_APPROVAL"

    # Thêm giấy tờ xác thực mẫu cho doanh nghiệp
    doc = CompanyDocument(
        company_id=company_id,
        doc_type=CompanyDocType.BUSINESS_LICENSE,
        file_url="https://storage.local/licenses/vinfast.pdf",
    )
    db.add(doc)
    db.commit()

    # 3. Admin xem danh sách doanh nghiệp chờ duyệt
    list_res = client.get(
        "/api/v1/admin/companies?verification_status=PENDING",
        headers=admin_headers,
    )
    assert list_res.status_code == 200
    assert any(c["id"] == company_id for c in list_res.json()["items"])

    # 4. Admin xem chi tiết kèm giấy phép kinh doanh
    detail_res = client.get(
        f"/api/v1/admin/companies/{company_id}",
        headers=admin_headers,
    )
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["name"] == "VinFast Auto"
    assert len(detail_data["documents"]) == 1
    assert detail_data["documents"][0]["doc_type"] == "BUSINESS_LICENSE"

    # 5. Admin phê duyệt doanh nghiệp
    approve_res = client.post(
        f"/api/v1/admin/companies/{company_id}/approve",
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["verification_status"] == VerificationStatus.APPROVED.value

    # Kiểm tra notification đã được tạo cho doanh nghiệp
    from sqlalchemy import select
    user_notis = db.scalars(select(Notification).where(Notification.user_id == user_id)).all()
    assert any(n.type == "COMPANY_APPROVED" for n in user_notis)

    # 6. Doanh nghiệp đăng nhập thành công sau khi duyệt
    success_login = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@vinfast.vn", "password": "Password@123"},
    )
    assert success_login.status_code == 200
    assert "access_token" in success_login.json()

    # 7. Phê duyệt lại doanh nghiệp đã duyệt -> 409 Conflict
    reapprove = client.post(
        f"/api/v1/admin/companies/{company_id}/approve",
        headers=admin_headers,
    )
    assert reapprove.status_code == 409


def test_reject_company(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)

    # Tạo công ty chờ duyệt
    company_user = make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL, email="reject_me@company.vn")
    company = Company(
        user_id=company_user.id,
        name="Công ty Ma",
        tax_code="0999999999",
        company_size=CompanySize.S_1_10,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(company)
    db.commit()

    # Admin từ chối phê duyệt
    reject_res = client.post(
        f"/api/v1/admin/companies/{company.id}/reject",
        json={"reject_reason": "Mã số thuế không tồn tại trên cổng quốc gia"},
        headers=admin_headers,
    )
    assert reject_res.status_code == 200
    body = reject_res.json()
    assert body["verification_status"] == VerificationStatus.REJECTED.value
    assert body["reject_reason"] == "Mã số thuế không tồn tại trên cổng quốc gia"

    # Người dùng vẫn chưa thể đăng nhập
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "reject_me@company.vn", "password": "Password@123"},
    )
    assert login_res.status_code == 403


def test_admin_companies_forbidden_for_student(client, make_user, auth_headers):
    student = make_user(UserRole.STUDENT)
    res = client.get("/api/v1/admin/companies", headers=auth_headers(student))
    assert res.status_code == 403


def test_approve_and_reject_locked_company_conflict(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)

    locked_user = make_user(UserRole.COMPANY, UserStatus.LOCKED, email="locked_comp@company.vn")
    company = Company(
        user_id=locked_user.id,
        name="Locked Company Ltd",
        tax_code="0911223344",
        company_size=CompanySize.S_1_10,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(company)
    db.commit()

    # Approve khi user bị khóa -> 409
    res_app = client.post(f"/api/v1/admin/companies/{company.id}/approve", headers=admin_headers)
    assert res_app.status_code == 409
    assert "khóa" in res_app.json()["error"]["message"]

    # Reject khi user bị khóa -> 409
    res_rej = client.post(
        f"/api/v1/admin/companies/{company.id}/reject",
        json={"reject_reason": "Any reason"},
        headers=admin_headers,
    )
    assert res_rej.status_code == 409
    assert "khóa" in res_rej.json()["error"]["message"]


def test_reject_state_transitions(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)

    # 1. Reject already rejected -> 409
    u1 = make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL, email="comp_rej@test.com")
    c1 = Company(
        user_id=u1.id,
        name="Company Rej",
        tax_code="0988776655",
        company_size=CompanySize.S_1_10,
        verification_status=VerificationStatus.REJECTED,
    )
    db.add(c1)
    db.commit()

    res1 = client.post(
        f"/api/v1/admin/companies/{c1.id}/reject",
        json={"reject_reason": "Again"},
        headers=admin_headers,
    )
    assert res1.status_code == 409
    assert "từ chối trước đó" in res1.json()["error"]["message"]

    # 2. Reject already approved -> 409
    u2 = make_user(UserRole.COMPANY, UserStatus.ACTIVE, email="comp_app@test.com")
    c2 = Company(
        user_id=u2.id,
        name="Company Approved",
        tax_code="0988776656",
        company_size=CompanySize.S_1_10,
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(c2)
    db.commit()

    res2 = client.post(
        f"/api/v1/admin/companies/{c2.id}/reject",
        json={"reject_reason": "Change mind"},
        headers=admin_headers,
    )
    assert res2.status_code == 409
    assert "đã được phê duyệt" in res2.json()["error"]["message"]
