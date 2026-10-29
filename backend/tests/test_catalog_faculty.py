"""Test mẫu cho một module: tạo, trùng lặp, phân quyền, danh sách, cập nhật, xóa mềm."""
from app.core.enums import UserRole

URL = "/api/v1/catalog/faculties"


def test_admin_creates_faculty(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    response = client.post(URL, json={"code": "CNTT", "name": "Công nghệ thông tin"}, headers=auth_headers(admin))
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "CNTT"
    assert body["is_active"] is True


def test_duplicate_code_is_conflict(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    headers = auth_headers(admin)
    client.post(URL, json={"code": "CNTT", "name": "Công nghệ thông tin"}, headers=headers)
    response = client.post(URL, json={"code": "CNTT", "name": "Tên khác"}, headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_student_cannot_create_but_can_read(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    student = make_user(UserRole.STUDENT)
    client.post(URL, json={"code": "KT", "name": "Kinh tế"}, headers=auth_headers(admin))

    assert client.post(URL, json={"code": "X", "name": "X"}, headers=auth_headers(student)).status_code == 403

    listing = client.get(URL, headers=auth_headers(student))
    assert listing.status_code == 200
    data = listing.json()
    assert data["total"] == 1
    assert data["items"][0]["code"] == "KT"
    assert {"items", "total", "page", "size", "pages"} <= set(data)


def test_update_and_deactivate(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    headers = auth_headers(admin)
    faculty_id = client.post(URL, json={"code": "CK", "name": "Cơ khí"}, headers=headers).json()["id"]

    updated = client.put(f"{URL}/{faculty_id}", json={"name": "Cơ khí động lực"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Cơ khí động lực"

    assert client.delete(f"{URL}/{faculty_id}", headers=headers).status_code == 204
    # Khoa đã ngừng hoạt động không còn trong danh sách mặc định
    assert client.get(URL, headers=headers).json()["total"] == 0
    assert client.get(URL, params={"include_inactive": True}, headers=headers).json()["total"] == 1
