def test_current_api_does_not_expose_academic_term_workflows(client):
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema["paths"]
    assert not any('lecturers' in path for path in paths)
    assert not any("internship-terms" in path or path.endswith("/me/internship") for path in paths)
    assert "/api/v1/admin/dashboard/flow-comparison" not in paths
    for path in ("/api/v1/jobs", "/api/v1/admin/jobs", "/api/v1/admin/dashboard/overview"):
        params = {parameter["name"] for parameter in paths[path]["get"].get("parameters", [])}
        assert "term_id" not in params
        assert "flow" not in params
    for name in ("JobCreate", "JobUpdate", "JobListItem", "AdminJobRead"):
        assert "term_id" not in schema["components"]["schemas"][name]["properties"]
