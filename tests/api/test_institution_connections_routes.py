from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_db,
    get_plaid_webhook_service,
    get_plaid_webhook_verifier,
)
from src.plaid.webhooks.verifier import PlaidWebhookVerificationError
from src.server import app


class FakeDb:
    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class AcceptingVerifier:
    def __init__(self):
        self.raw_body = None

    def verify(self, raw_body, plaid_verification):
        self.raw_body = raw_body


class RejectingVerifier:
    def verify(self, raw_body, plaid_verification):
        raise PlaidWebhookVerificationError("bad signature")


class RecordingWebhookService:
    def __init__(self):
        self.payloads = []

    def dispatch(self, db, payload):
        self.payloads.append(payload)


def _override_db():
    yield FakeDb()


def test_valid_webhook_returns_accepted():
    verifier = AcceptingVerifier()
    service = RecordingWebhookService()
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_plaid_webhook_verifier] = lambda: verifier
    app.dependency_overrides[get_plaid_webhook_service] = lambda: service

    try:
        response = TestClient(app).post(
            "/api/v1/plaid/webhooks",
            headers={"Plaid-Verification": "signed"},
            json={
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "SYNC_UPDATES_AVAILABLE",
                "item_id": "item-1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert verifier.raw_body is not None
    assert service.payloads[0].webhook_code == "SYNC_UPDATES_AVAILABLE"


def test_invalid_webhook_signature_returns_unauthorized():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_plaid_webhook_verifier] = lambda: RejectingVerifier()
    app.dependency_overrides[get_plaid_webhook_service] = lambda: RecordingWebhookService()

    try:
        response = TestClient(app).post(
            "/api/v1/plaid/webhooks",
            headers={"Plaid-Verification": "bad"},
            json={
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "SYNC_UPDATES_AVAILABLE",
                "item_id": "item-1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_unknown_valid_webhook_returns_accepted():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_plaid_webhook_verifier] = lambda: AcceptingVerifier()
    app.dependency_overrides[get_plaid_webhook_service] = lambda: RecordingWebhookService()

    try:
        response = TestClient(app).post(
            "/api/v1/plaid/webhooks",
            headers={"Plaid-Verification": "signed"},
            json={
                "webhook_type": "UNKNOWN",
                "webhook_code": "UNKNOWN",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
