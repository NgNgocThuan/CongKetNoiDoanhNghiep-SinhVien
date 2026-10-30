import pytest

from app.core.enums import ApplicationStatus
from app.models import Application
from app.services import matching_service
from tests.school_factories import domain

BASE = "/api/v1/admin/dashboard"
ENDPOINTS = [
    "overview",
    "breakdown",
    "top-skills",
    "skill-gap",
    "match-rate",
    "trends",
    "flow-comparison",
]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_dashboard_aggregates_and_roles(client, db, make_user, auth_headers, endpoint, monkeypatch):
    d = domain(db, make_user)
    monkeypatch.setattr("app.core.config.settings.AI_API_KEY", "")
    db.add(
        Application(
            student_id=d.student.id,
            job_id=d.job.id,
            cv_id=d.cv.id,
            current_status=ApplicationStatus.HIRED,
        )
    )
    db.commit()
    matching_service.get_or_compute_match(db, d.student, d.job)
    response = client.get(f"{BASE}/{endpoint}", headers=auth_headers(d.admin))
    assert response.status_code == 200, response.text
    result = response.json()
    if endpoint == "overview":
        assert result == {
            "students": 1,
            "companies": 2,
            "jobs": 1,
            "applications": 1,
            "interviews": 0,
            "hired": 1,
        }
    elif endpoint == "breakdown":
        assert result["items"][0]["count"] == 1
    elif endpoint == "top-skills":
        assert result["items"][0]["name"] == "Python" and result["items"][0]["required_jobs"] == 1
    elif endpoint == "skill-gap":
        assert result["items"][0]["students_with_skill"] == 1
        assert result["items"][0]["students_missing_skill"] == 0
    elif endpoint == "match-rate":
        assert result["items"][0]["match_rate"] == 100
    elif endpoint == "trends":
        assert result["items"][0]["jobs"] == 1 and result["items"][0]["applications"] == 1
    else:
        assert result["items"][0]["flow"] == "free" and result["items"][0]["hired"] == 1
    assert client.get(f"{BASE}/{endpoint}", headers=auth_headers(d.student_user)).status_code == 403
    assert (
        client.get(
            f"{BASE}/{endpoint}?date_from=2027-01-01&date_to=2026-01-01",
            headers=auth_headers(d.admin),
        ).status_code
        == 422
    )
    response = client.get(f"{BASE}/{endpoint}?date_to=2000-01-01", headers=auth_headers(d.admin))
    assert response.status_code == 200, response.text
    if endpoint == "overview":
        assert response.json()["jobs"] == 0


def test_dashboard_group_filters(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    headers = auth_headers(d.admin)
    for group in ("major", "faculty", "cohort", "term"):
        response = client.get(f"{BASE}/breakdown?group_by={group}", headers=headers)
        assert response.status_code == 200, response.text
    assert client.get(f"{BASE}/breakdown?group_by=unknown", headers=headers).status_code == 422
    response = client.get(f"{BASE}/overview?major_id=999", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["students"] == 0


def test_dashboard_pagination_and_skill_trends(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    for endpoint in (
        "breakdown",
        "top-skills",
        "skill-gap",
        "match-rate",
        "trends",
        "flow-comparison",
    ):
        response = client.get(f"{BASE}/{endpoint}?page=1&size=1", headers=auth_headers(d.admin))
        assert response.status_code == 200, response.text
        assert response.json()["size"] == 1
    response = client.get(f"{BASE}/trends", headers=auth_headers(d.admin))
    assert response.json()["items"][0]["skills"][0]["name"] == "Python"


def test_seed_reports_work(db):
    from app.schemas.dashboard import DashboardFilter
    from app.services import dashboard_service, export_service
    from scripts.seed import seed

    seed(db)
    filters = DashboardFilter()
    assert dashboard_service.overview(db, filters)["students"] >= 1
    assert export_service.export_excel(db, "students", filters).startswith(b"PK")
    assert export_service.export_dashboard_pdf(db, filters).startswith(b"%PDF")


def test_swagger_documents_school_and_analytics_endpoints(client):
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema["paths"]
    prefixes = (
        "/api/v1/catalog",
        "/api/v1/admin/students",
        "/api/v1/admin/lecturers",
        "/api/v1/internship-terms",
        "/api/v1/matching",
        "/api/v1/admin/dashboard",
        "/api/v1/admin/exports",
    )
    for path, operations in paths.items():
        if not path.startswith(prefixes):
            continue
        for method, operation in operations.items():
            if method not in {"get", "post", "put", "delete"}:
                continue
            assert operation.get("summary"), (path, method)
            assert operation.get("security"), (path, method)
            response = (
                operation["responses"].get("200")
                or operation["responses"].get("201")
                or operation["responses"].get("202")
            )
            if response:
                assert response.get("content"), (path, method)
    assert "/api/v1/matching/jobs/recommended" in paths
    assert "/api/v1/admin/exports/dashboard.pdf" in paths
