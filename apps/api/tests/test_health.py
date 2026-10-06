"""Process health contract tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_is_database_independent() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "energy-dashboard-api",
        "version": "0.1.0",
    }
    assert response.headers["X-Request-ID"] == "test-request-id"
