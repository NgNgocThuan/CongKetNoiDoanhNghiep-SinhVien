"""Test quản lý giảng viên: tạo, trùng mã, phân quyền, sửa, ngừng hoạt động."""
from app.core.enums import UserRole
from app.models import Faculty

URL = "/api/v1/admin/lecturers"


def _faculty(db):
    faculty = Faculty(code="CNTT", name="Công nghệ thông tin")
    db.add(faculty)
    db.commit()
    return faculty


def test_lecturer_lifecycle(client, db, make_user, auth_headers):
    headers = auth_headers(make_user(UserRole.ADMIN))
    faculty = _faculty(db)
    body = {"code": "GV001", "full_name": "Nguyễn Văn A", "faculty_id": faculty.id, "email": "gv1@school.vn"}
    created = client.post(URL, json=body, headers=headers)
    assert created.status_code == 201 and created.json()["is_active"] is True
    lid = created.json()["id"]

    assert client.post(URL, json=body, headers=headers).status_code == 409
    assert client.post(URL, json={**body, "code": "GV002", "faculty_id": 999}, headers=headers).status_code == 404
    assert client.post(URL, json={**body, "code": "GV003", "email": "sai"}, headers=headers).status_code == 422

    assert client.put(f"{URL}/{lid}", json={"phone": "0900"}, headers=headers).json()["phone"] == "0900"
    assert client.get(f"{URL}/{lid}", headers=headers).json()["code"] == "GV001"
    assert client.get(URL, params={"q": "nguyễn", "faculty_id": faculty.id}, headers=headers).json()["total"] == 1

    assert client.delete(f"{URL}/{lid}", headers=headers).status_code == 204
    assert client.get(URL, headers=headers).json()["total"] == 0
    assert client.get(URL, params={"include_inactive": True}, headers=headers).json()["total"] == 1


def test_lecturer_admin_only(client, make_user, auth_headers):
    student = auth_headers(make_user(UserRole.STUDENT))
    assert client.get(URL, headers=student).status_code == 403
    assert client.post(URL, json={"full_name": "X", "faculty_id": 1}, headers=student).status_code == 403
