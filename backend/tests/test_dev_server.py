"""Test endpoint đăng nhập tạm của scripts/dev_server.py (dùng cho nút Authorize của Swagger)."""
import scripts.dev_server  # noqa: F401  (import để gắn endpoint vào app)
from app.core.enums import UserRole

LOGIN = "/api/v1/auth/token"


def test_login_form_gives_working_token(client, make_user):
    admin = make_user(UserRole.ADMIN, email="admin@x.vn")
    response = client.post(LOGIN, data={"username": "admin@x.vn", "password": "Password@123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert client.get("/api/v1/catalog/faculties", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert admin.id


def test_login_rejects_wrong_password(client, make_user):
    make_user(UserRole.ADMIN, email="admin@x.vn")
    assert client.post(LOGIN, data={"username": "admin@x.vn", "password": "sai"}).status_code == 401
    assert client.post(LOGIN, data={"username": "khong@co.vn", "password": "Password@123"}).status_code == 401
