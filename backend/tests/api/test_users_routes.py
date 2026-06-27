from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.dependencies import get_db, get_user_service
from src.infrastructure.firebase.firebase import get_firebase_identity
from src.server import app


class DummySession:
    def commit(self):
        return None

    def refresh(self, _user):
        return None

    def rollback(self):
        return None


class DummyUserService:
    def __init__(self, user):
        self.user = user
        self.calls = 0

    def get_or_create_me(self, db, firebase_identity):
        self.calls += 1
        return self.user


def override_db():
    return DummySession()


def test_users_me_creates_user_when_auth_mode_is_open(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "open")
    monkeypatch.delenv("AUTHORIZED_EMAILS", raising=False)

    user = SimpleNamespace(
        id=uuid4(),
        email="viewer@example.com",
        firebase_uid="firebase-123",
        name=None,
    )
    user_service = DummyUserService(user)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_firebase_identity] = lambda: {
        "uid": "firebase-123",
        "email": "viewer@example.com",
    }

    response = TestClient(app).post("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["email"] == "viewer@example.com"
    assert user_service.calls == 1

    app.dependency_overrides.clear()


def test_users_me_rejects_non_allowlisted_email_in_restricted_mode(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "restricted")
    monkeypatch.setenv("AUTHORIZED_EMAILS", "owner@example.com")
    monkeypatch.setenv("ACCESS_CONTACT", "Roy Zhao")

    user = SimpleNamespace(
        id=uuid4(),
        email="viewer@example.com",
        firebase_uid="firebase-123",
        name=None,
    )
    user_service = DummyUserService(user)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_firebase_identity] = lambda: {
        "uid": "firebase-123",
        "email": "viewer@example.com",
    }

    response = TestClient(app).post("/api/v1/users/me")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Access to this Lantern deployment is limited to approved email addresses. Contact Roy Zhao for access."
    }
    assert user_service.calls == 0

    app.dependency_overrides.clear()
