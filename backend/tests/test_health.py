def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/v1/catalog/faculties")
    assert response.status_code == 401
