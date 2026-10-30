"""Test danh mục: ngành, lĩnh vực, loại hình công việc, kỹ năng, alias và normalize_skill_names."""
from app.core.enums import UserRole
from app.services import catalog_service

BASE = "/api/v1/catalog"


def _admin(make_user, auth_headers):
    return auth_headers(make_user(UserRole.ADMIN))


def _faculty(client, headers, code="CNTT"):
    return client.post(f"{BASE}/faculties", json={"code": code, "name": f"Khoa {code}"}, headers=headers).json()["id"]


# ---------------------------------------------------------------- Major
def test_major_crud_and_filter(client, make_user, auth_headers):
    headers = _admin(make_user, auth_headers)
    f1, f2 = _faculty(client, headers, "A"), _faculty(client, headers, "B")
    created = client.post(
        f"{BASE}/majors", json={"faculty_id": f1, "code": "KTPM", "name": "Kỹ thuật phần mềm"}, headers=headers
    )
    assert created.status_code == 201
    client.post(f"{BASE}/majors", json={"faculty_id": f2, "code": "KT", "name": "Kế toán"}, headers=headers)

    only_f1 = client.get(f"{BASE}/majors", params={"faculty_id": f1}, headers=headers).json()
    assert only_f1["total"] == 1 and only_f1["items"][0]["code"] == "KTPM"

    mid = created.json()["id"]
    assert client.put(f"{BASE}/majors/{mid}", json={"name": "KTPM mới"}, headers=headers).json()["name"] == "KTPM mới"
    assert client.delete(f"{BASE}/majors/{mid}", headers=headers).status_code == 204
    assert client.get(f"{BASE}/majors", headers=headers).json()["total"] == 1


def test_major_requires_existing_faculty_and_unique_code(client, make_user, auth_headers):
    headers = _admin(make_user, auth_headers)
    assert client.post(
        f"{BASE}/majors", json={"faculty_id": 999, "code": "X", "name": "X"}, headers=headers
    ).status_code == 404
    fid = _faculty(client, headers)
    body = {"faculty_id": fid, "code": "KTPM", "name": "A"}
    assert client.post(f"{BASE}/majors", json=body, headers=headers).status_code == 201
    assert client.post(f"{BASE}/majors", json=body, headers=headers).status_code == 409


def test_student_cannot_write_catalog(client, make_user, auth_headers):
    student = auth_headers(make_user(UserRole.STUDENT))
    assert client.post(f"{BASE}/industries", json={"name": "X"}, headers=student).status_code == 403
    assert client.post(f"{BASE}/skills", json={"name": "X"}, headers=student).status_code == 403
    assert client.get(f"{BASE}/industries", headers=student).status_code == 200


# ---------------------------------------------------------------- Industry / JobType
def test_industry_and_job_type(client, make_user, auth_headers):
    headers = _admin(make_user, auth_headers)
    assert client.post(f"{BASE}/industries", json={"name": "Phần mềm"}, headers=headers).status_code == 201
    assert client.post(f"{BASE}/industries", json={"name": "Phần mềm"}, headers=headers).status_code == 409

    jt = client.post(f"{BASE}/job-types", json={"code": "INTERN", "name": "Thực tập sinh"}, headers=headers)
    assert jt.status_code == 201
    assert client.post(f"{BASE}/job-types", json={"code": "INTERN", "name": "Khác"}, headers=headers).status_code == 409
    assert client.delete(f"{BASE}/job-types/{jt.json()['id']}", headers=headers).status_code == 204
    assert client.get(f"{BASE}/job-types", headers=headers).json()["total"] == 0


# ---------------------------------------------------------------- Skill + alias
def test_skill_search_and_aliases(client, make_user, auth_headers):
    headers = _admin(make_user, auth_headers)
    sid = client.post(f"{BASE}/skills", json={"name": "React", "category": "Frontend"}, headers=headers).json()["id"]
    client.post(f"{BASE}/skills", json={"name": "Python"}, headers=headers)

    alias = client.post(f"{BASE}/skills/{sid}/aliases", json={"alias": "ReactJS"}, headers=headers)
    assert alias.status_code == 201
    # Alias trùng (khác hoa thường) và alias trùng tên kỹ năng đều bị chặn
    assert client.post(f"{BASE}/skills/{sid}/aliases", json={"alias": "reactjs"}, headers=headers).status_code == 409
    assert client.post(f"{BASE}/skills/{sid}/aliases", json={"alias": "python"}, headers=headers).status_code == 409
    # Tên kỹ năng mới không được trùng alias
    assert client.post(f"{BASE}/skills", json={"name": "reactjs"}, headers=headers).status_code == 409

    found = client.get(f"{BASE}/skills/search", params={"q": "reactj"}, headers=headers).json()
    assert [s["name"] for s in found] == ["React"]
    assert client.get(f"{BASE}/skills/{sid}", headers=headers).json()["name"] == "React"
    assert len(client.get(f"{BASE}/skills/{sid}/aliases", headers=headers).json()) == 1

    assert client.delete(f"{BASE}/skills/{sid}/aliases/{alias.json()['id']}", headers=headers).status_code == 204
    assert client.delete(f"{BASE}/skills/{sid}/aliases/{alias.json()['id']}", headers=headers).status_code == 404


def test_normalize_skill_names(client, make_user, auth_headers, db):
    headers = _admin(make_user, auth_headers)
    react = client.post(f"{BASE}/skills", json={"name": "React"}, headers=headers).json()["id"]
    client.post(f"{BASE}/skills", json={"name": "Python"}, headers=headers)
    old = client.post(f"{BASE}/skills", json={"name": "Old"}, headers=headers).json()["id"]
    client.post(f"{BASE}/skills/{react}/aliases", json={"alias": "ReactJS"}, headers=headers)
    client.delete(f"{BASE}/skills/{old}", headers=headers)

    result = catalog_service.normalize_skill_names(
        db, ["  reactjs ", "PYTHON", "react", "Unknown", "", "old"]
    )
    # alias + tên khác hoa thường được nhận; trùng (React) chỉ giữ một; tên lạ, rỗng, đã ngừng bị bỏ
    assert [s.name for s in result] == ["React", "Python"]
    assert catalog_service.normalize_skill_names(db, []) == []
