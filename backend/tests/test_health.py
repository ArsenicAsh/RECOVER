from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_shape():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"ok", "unavailable"}
