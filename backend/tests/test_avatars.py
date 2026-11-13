from io import BytesIO

import pytest
from PIL import Image

from app.core.enums import UserRole


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.STUDENT, UserRole.COMPANY, UserRole.CLIENT])
def test_avatar_upload_and_view(client, db, make_user, auth_headers, role):
    owner = make_user(role)
    viewer = make_user(UserRole.STUDENT)
    data = BytesIO()
    Image.new("RGB", (120, 80), "green").save(data, "PNG")
    assert client.put("/api/v1/auth/me/avatar", files={"file": ("photo.png", data.getvalue(), "image/png")}).status_code == 401
    response = client.put("/api/v1/auth/me/avatar", headers=auth_headers(owner), files={"file": ("photo.png", data.getvalue(), "image/png")})
    assert response.status_code == 200, response.text
    response = client.get(f"/api/v1/auth/users/{owner.id}/avatar", headers=auth_headers(viewer))
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    image = Image.open(BytesIO(response.content))
    assert image.size == (384, 384)
    assert client.get(f"/api/v1/auth/users/{viewer.id}/avatar", headers=auth_headers(viewer)).status_code == 204
    rejected = client.put("/api/v1/auth/me/avatar", headers=auth_headers(owner), files={"file": ("fake.png", b"<script>bad</script>", "image/png")})
    assert rejected.status_code == 400
    assert client.get(f"/api/v1/auth/users/{owner.id}/avatar", headers=auth_headers(viewer)).content == response.content


def test_demo_seed_is_repeatable(db):
    from sqlalchemy import func, select

    from app.models import Industry, Job
    from scripts.seed_demo_catalog import INDUSTRIES, seed

    assert seed(db) == 12
    assert seed(db) == 0
    assert db.scalar(select(func.count(Job.id))) == 12
    assert db.scalar(select(func.count(Industry.id))) == len(INDUSTRIES)
