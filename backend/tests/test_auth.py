"""Test toàn diện phân hệ Xác thực (Auth). Người phụ trách: TV1."""
from datetime import timedelta

import pytest

from app.core.enums import CompanySize, UserRole, UserStatus, VerificationStatus
from app.core.security import generate_reset_token
from app.models import Admin, Company, PasswordResetToken, User
from app.services.auth_service import clear_auth_security_state, create_activation_token
from app.utils.datetime_utils import utcnow


@pytest.fixture(autouse=True)
def _reset_security_state():
    clear_auth_security_state()
    yield
    clear_auth_security_state()


def test_login_success(client, make_user):
    make_user(UserRole.STUDENT, UserStatus.ACTIVE, email="student@test.com")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@test.com", "password": "Password@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_oauth2_form(client, make_user):
    user = make_user(UserRole.ADMIN, UserStatus.ACTIVE, email="admin_oauth@test.com")
    response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "Password@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_password_or_email(client, make_user):
    make_user(UserRole.STUDENT, UserStatus.ACTIVE, email="user@test.com")

    # Sai mật khẩu
    res_wrong_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "WrongPassword"},
    )
    assert res_wrong_pw.status_code == 401
    assert res_wrong_pw.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Email không tồn tại
    res_no_email = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "Password@123"},
    )
    assert res_no_email.status_code == 401


def test_login_blocked_by_status(client, make_user):
    # LOCKED
    make_user(UserRole.STUDENT, UserStatus.LOCKED, email="locked@test.com")
    res_locked = client.post(
        "/api/v1/auth/login",
        json={"email": "locked@test.com", "password": "Password@123"},
    )
    assert res_locked.status_code == 403
    assert res_locked.json()["error"]["code"] == "ACCOUNT_LOCKED"

    # PENDING_ACTIVATION
    make_user(UserRole.STUDENT, UserStatus.PENDING_ACTIVATION, email="pending_act@test.com")
    res_pending_act = client.post(
        "/api/v1/auth/login",
        json={"email": "pending_act@test.com", "password": "Password@123"},
    )
    assert res_pending_act.status_code == 403
    assert res_pending_act.json()["error"]["code"] == "ACCOUNT_NOT_ACTIVE"

    # PENDING_APPROVAL
    make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL, email="pending_app@test.com")
    res_pending_app = client.post(
        "/api/v1/auth/login",
        json={"email": "pending_app@test.com", "password": "Password@123"},
    )
    assert res_pending_app.status_code == 403
    assert res_pending_app.json()["error"]["code"] == "ACCOUNT_PENDING_APPROVAL"


def test_refresh_token(client, make_user, db):
    user = make_user(UserRole.STUDENT, UserStatus.ACTIVE)
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Password@123"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Refresh thành công
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    new_refresh_token = refresh_res.json()["refresh_token"]

    # Dùng access token làm refresh token -> Bị từ chối
    access_token = login_res.json()["access_token"]
    bad_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert bad_res.status_code == 401

    # User bị khóa thì không refresh được
    user_db = db.get(User, user.id)
    user_db.status = UserStatus.LOCKED
    db.commit()

    locked_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh_token},
    )
    assert locked_refresh.status_code == 403


def test_get_me(client, make_user, auth_headers, db):
    # Admin
    admin_user = make_user(UserRole.ADMIN, email="admin_me@test.com")
    admin_profile = Admin(user_id=admin_user.id, full_name="Admin Boss", position="Trưởng phòng")
    db.add(admin_profile)
    db.commit()

    res_admin = client.get("/api/v1/auth/me", headers=auth_headers(admin_user))
    assert res_admin.status_code == 200
    body_admin = res_admin.json()
    assert body_admin["email"] == "admin_me@test.com"
    assert body_admin["admin"]["full_name"] == "Admin Boss"

    # Company
    comp_user = make_user(UserRole.COMPANY, email="comp_me@test.com")
    comp_profile = Company(
        user_id=comp_user.id,
        name="Tập đoàn FPT",
        tax_code="0101234567",
        company_size=CompanySize.S_1000_PLUS,
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(comp_profile)
    db.commit()

    res_comp = client.get("/api/v1/auth/me", headers=auth_headers(comp_user))
    assert res_comp.status_code == 200
    body_comp = res_comp.json()
    assert body_comp["company"]["name"] == "Tập đoàn FPT"


def test_change_password(client, make_user, auth_headers):
    user = make_user(UserRole.STUDENT, email="change_pwd@test.com")
    headers = auth_headers(user)

    # Đổi mật khẩu thành công
    res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "Password@123", "new_password": "NewSecretPassword@456"},
        headers=headers,
    )
    assert res.status_code == 200

    # Đăng nhập bằng mật khẩu mới
    res_login_new = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "NewSecretPassword@456"},
    )
    assert res_login_new.status_code == 200

    # Sai mật khẩu cũ
    res_wrong_old = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "WrongOldPassword", "new_password": "AnotherPassword@789"},
        headers=headers,
    )
    assert res_wrong_old.status_code == 400

    # Trùng mật khẩu cũ
    res_same = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "NewSecretPassword@456", "new_password": "NewSecretPassword@456"},
        headers=headers,
    )
    assert res_same.status_code == 400


def test_forgot_and_reset_password(client, make_user, db):
    user = make_user(UserRole.STUDENT, email="forgot_pwd@test.com")

    # Forgot password với email tồn tại -> trả 200
    res_exist = client.post("/api/v1/auth/forgot-password", json={"email": "forgot_pwd@test.com"})
    assert res_exist.status_code == 200

    # Forgot password với email KHÔNG tồn tại -> vẫn trả 200 (chống quét user)
    res_nonexist = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@test.com"})
    assert res_nonexist.status_code == 200

    # Sinh token đặt lại mật khẩu thủ công để test endpoint reset-password
    raw_token = create_activation_token(db, user.id)

    # Đặt lại mật khẩu thành công
    res_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "ResetPassword@123"},
    )
    assert res_reset.status_code == 200

    # Đăng nhập bằng mật khẩu mới
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": "forgot_pwd@test.com", "password": "ResetPassword@123"},
    )
    assert res_login.status_code == 200

    # Dùng lại token lần 2 -> Bị từ chối
    res_reuse = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherReset@123"},
    )
    assert res_reuse.status_code == 400
    assert res_reuse.json()["error"]["code"] == "TOKEN_USED"

    # Token hết hạn
    raw_expired, hash_expired = generate_reset_token()
    prt_expired = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_expired,
        expires_at=utcnow() - timedelta(minutes=5),
    )
    db.add(prt_expired)
    db.commit()

    res_expired = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_expired, "new_password": "ResetPassword@123"},
    )
    assert res_expired.status_code == 400
    assert res_expired.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_activate_student_account(client, make_user, db):
    user = make_user(UserRole.STUDENT, UserStatus.PENDING_ACTIVATION, email="student_act@test.com")
    raw_token = create_activation_token(db, user.id)

    # Kích hoạt tài khoản
    res = client.post(
        "/api/v1/auth/activate",
        json={"token": raw_token, "new_password": "MyActivePassword@123"},
    )
    assert res.status_code == 200

    # Đăng nhập ngay sau khi kích hoạt
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": "student_act@test.com", "password": "MyActivePassword@123"},
    )
    assert res_login.status_code == 200

    # Cố tình kích hoạt lại với token mới -> Bị báo xung đột vì đã ACTIVE
    raw_token_2 = create_activation_token(db, user.id)
    res_repeat = client.post(
        "/api/v1/auth/activate",
        json={"token": raw_token_2, "new_password": "MyActivePassword@123"},
    )
    assert res_repeat.status_code == 409


def test_register_company(client, db):
    data = {
        "email": "hr@startup.vn",
        "password": "Password@123",
        "company_name": "Startup Vietnam Tech",
        "tax_code": "0319876543",
        "contact_name": "Nguyen Van A",
        "contact_phone": "0912345678",
    }
    # Đăng ký thành công
    res = client.post("/api/v1/auth/register-company", json=data)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == UserStatus.PENDING_APPROVAL.value
    assert body["verification_status"] == VerificationStatus.PENDING.value

    # Trùng email -> 409
    res_dup_email = client.post(
        "/api/v1/auth/register-company",
        json={**data, "tax_code": "0319876544"},
    )
    assert res_dup_email.status_code == 409

    # Trùng mã số thuế -> 409
    res_dup_tax = client.post(
        "/api/v1/auth/register-company",
        json={**data, "email": "other@startup.vn"},
    )
    assert res_dup_tax.status_code == 409


def test_logout(client, make_user):
    user = make_user(UserRole.STUDENT, email="logout_test@test.com")
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Password@123"},
    )
    tokens = login_res.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Đang hoạt động bình thường
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200

    # Đăng xuất kèm refresh_token
    res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert res.status_code == 200

    # Gọi lại /auth/me bằng access_token cũ -> 401 TOKEN_REVOKED
    me_revoked = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_revoked.status_code == 401
    assert me_revoked.json()["error"]["code"] == "TOKEN_REVOKED"

    # Gọi lại /auth/refresh bằng refresh_token cũ -> 401 TOKEN_REVOKED
    ref_revoked = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_revoked.status_code == 401
    assert ref_revoked.json()["error"]["code"] == "TOKEN_REVOKED" 


def test_login_pending_activation_null_password(client, db):
    user = User(
        email="imported_student@test.com",
        password_hash=None,
        role=UserRole.STUDENT,
        status=UserStatus.PENDING_ACTIVATION,
    )
    db.add(user)
    db.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "imported_student@test.com", "password": "AnyPassword@123"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ACCOUNT_NOT_ACTIVE"


def test_forgot_password_pending_activation_ignores_request(client, db):
    user = User(
        email="pending_forgot@test.com",
        password_hash=None,
        role=UserRole.STUDENT,
        status=UserStatus.PENDING_ACTIVATION,
    )
    db.add(user)
    db.commit()

    res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "pending_forgot@test.com"},
    )
    assert res.status_code == 200
    # Đảm bảo không token nào được sinh ra cho user này
    tokens = db.query(PasswordResetToken).filter_by(user_id=user.id).all()
    assert len(tokens) == 0


def test_reset_password_pending_activation_user_rejected(client, db):
    user = User(
        email="pending_reset@test.com",
        password_hash=None,
        role=UserRole.STUDENT,
        status=UserStatus.PENDING_ACTIVATION,
    )
    db.add(user)
    db.commit()

    raw_token = create_activation_token(db, user.id)

    res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewSecret@123"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "ACCOUNT_NOT_ACTIVE"

    # Token chưa bị tiêu thụ (unburnt)
    token_in_db = db.query(PasswordResetToken).filter_by(user_id=user.id).first()
    assert token_in_db.used_at is None


def test_activate_student_invalidates_all_active_tokens(client, make_user, db):
    user = make_user(UserRole.STUDENT, UserStatus.PENDING_ACTIVATION, email="multi_token@test.com")
    raw_token_1 = create_activation_token(db, user.id)
    raw_token_2 = create_activation_token(db, user.id)

    # Kích hoạt bằng token 2
    res = client.post(
        "/api/v1/auth/activate",
        json={"token": raw_token_2, "new_password": "ActivatedPass@123"},
    )
    assert res.status_code == 200

    # Cả hai token đều phải có used_at
    tokens = db.query(PasswordResetToken).filter_by(user_id=user.id).all()
    assert len(tokens) == 2
    for t in tokens:
        assert t.used_at is not None

    # Thử dùng token 1 -> báo TOKEN_USED
    res_reuse_1 = client.post(
        "/api/v1/auth/activate",
        json={"token": raw_token_1, "new_password": "ActivatedPass@123"},
    )
    assert res_reuse_1.status_code == 400
    assert res_reuse_1.json()["error"]["code"] == "TOKEN_USED"


def test_activate_non_student_account_forbidden(client, make_user, db):
    user = make_user(UserRole.COMPANY, UserStatus.PENDING_ACTIVATION, email="company_fake_act@test.com")
    raw_token = create_activation_token(db, user.id)

    res = client.post(
        "/api/v1/auth/activate",
        json={"token": raw_token, "new_password": "CompanyPass@123"},
    )
    assert res.status_code == 403
    assert "sinh viên" in res.json()["error"]["message"]



def test_refresh_token_rotation(client, make_user):
    user = make_user(UserRole.STUDENT, email="rotation@test.com")
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Password@123"},
    )
    r1 = login_res.json()["refresh_token"]

    # Refresh lần 1 -> thành công, trả về r2
    ref_res1 = client.post("/api/v1/auth/refresh", json={"refresh_token": r1})
    assert ref_res1.status_code == 200
    r2 = ref_res1.json()["refresh_token"]
    assert r2 != r1

    # Dùng lại r1 lần 2 -> 401 TOKEN_REVOKED
    ref_res_replay = client.post("/api/v1/auth/refresh", json={"refresh_token": r1})
    assert ref_res_replay.status_code == 401
    assert ref_res_replay.json()["error"]["code"] == "TOKEN_REVOKED"

    # Dùng r2 hợp lệ -> 200
    ref_res2 = client.post("/api/v1/auth/refresh", json={"refresh_token": r2})
    assert ref_res2.status_code == 200


def test_login_brute_force_lockout(client, make_user):
    user = make_user(UserRole.STUDENT, email="brute_force@test.com")

    # Sai 5 lần liên tiếp
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "WrongPassword@123"},
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Lần thứ 6 bị khóa 429 TOO_MANY_ATTEMPTS
    locked_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Password@123"},
    )
    assert locked_res.status_code == 429
    assert locked_res.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"


def test_forgot_password_cooldown(client, make_user, db):
    user = make_user(UserRole.STUDENT, email="cooldown_forgot@test.com")

    # Lần 1: Tạo token thành công
    res1 = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert res1.status_code == 200
    tokens1 = db.query(PasswordResetToken).filter_by(user_id=user.id).all()
    assert len(tokens1) == 1

    # Lần 2 ngay lập tức: Trả về 200 nhưng không sinh token mới do cooldown
    res2 = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert res2.status_code == 200
    tokens2 = db.query(PasswordResetToken).filter_by(user_id=user.id).all()
    assert len(tokens2) == 1
