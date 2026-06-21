from fastapi.testclient import TestClient

import src.server as server_module
from src.server import app


def test_live_health_returns_ok():
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_health_returns_ok_when_database_is_ready(monkeypatch):
    monkeypatch.setattr(server_module, "database_ready", lambda: True)

    response = TestClient(app).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_health_returns_service_unavailable_when_database_is_down(monkeypatch):
    monkeypatch.setattr(server_module, "database_ready", lambda: False)

    response = TestClient(app).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "detail": "Database unavailable",
    }
