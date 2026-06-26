from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import src.api.routes.plaid as plaid_routes
from src.api.dependencies import (
    get_db,
    get_plaid_webhook_service,
    get_plaid_webhook_verifier,
)
from src.exceptions import ServiceUnavailableError
from src.modules.plaid_webhooks.verifier import PlaidWebhookVerificationError
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


class FakeTransactionalDb:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FailingKms:
    def encrypt_secret(self, _plaintext):
        raise ServiceUnavailableError(
            detail=(
                "KMS is unavailable: AWS credentials were not found. "
                "Configure AWS credentials before linking an institution."
            )
        )


class FakeWorkflow:
    def link_new_connection(self, db, kms, user, plaid_client, link_public_token):
        plaid_item_id = "item-123"
        plaid_access_token = "access-sandbox-token"
        institution_id = "ins_123"
        institution_name = "Test Bank"
        membership = SimpleNamespace(household_id=uuid4())
        connection_repo = SimpleNamespace(create_encrypted=lambda **kwargs: kms.encrypt_secret(plaid_access_token))
        connection_service = SimpleNamespace(connection_repo=connection_repo)

        if membership is None:
            raise AssertionError("membership should exist in test")

        connection_service.connection_repo.create_encrypted(
            db=db,
            kms=kms,
            user=user,
            household_id=membership.household_id,
            plaid_item_id=plaid_item_id,
            plaid_access_token=plaid_access_token,
            institution_id=institution_id,
            institution_name=institution_name,
        )


class RecordingSyncJobsRepo:
    def __init__(self):
        self.cancelled = []

    def cancel_queued_or_running_for_connection(
        self, db, institution_connection_id, last_error=None
    ):
        self.cancelled.append((institution_connection_id, last_error))


class RecordingConnectionService:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def revoke_connection(self, db, kms, sync_jobs_repo, user_id, connection_id):
        self.calls.append(
            {
                "db": db,
                "kms": kms,
                "sync_jobs_repo": sync_jobs_repo,
                "user_id": user_id,
                "connection_id": connection_id,
            }
        )
        if self.error is not None:
            raise self.error


def test_add_item_returns_service_unavailable_when_kms_credentials_are_missing():
    db = FakeTransactionalDb()
    app.dependency_overrides[plaid_routes.get_db] = lambda: db
    app.dependency_overrides[plaid_routes.get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[plaid_routes.get_kms_service] = lambda: FailingKms()
    app.dependency_overrides[plaid_routes.get_plaid_client] = lambda: SimpleNamespace()
    app.dependency_overrides[plaid_routes.get_link_institution_connection_workflow] = (
        lambda: FakeWorkflow()
    )

    try:
        response = TestClient(app).post(
            "/api/v1/plaid/item",
            data={"link_public_token": "public-sandbox-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "KMS is unavailable: AWS credentials were not found. "
            "Configure AWS credentials before linking an institution."
        )
    }
    assert db.commits == 0
    assert db.rollbacks == 1


def test_revoke_item_returns_no_content_and_commits():
    db = FakeTransactionalDb()
    user_id = uuid4()
    connection_id = uuid4()
    kms = SimpleNamespace()
    connection_service = RecordingConnectionService()
    sync_jobs_repo = RecordingSyncJobsRepo()
    app.dependency_overrides[plaid_routes.get_db] = lambda: db
    app.dependency_overrides[plaid_routes.get_current_user] = lambda: SimpleNamespace(id=user_id)
    app.dependency_overrides[plaid_routes.get_kms_service] = lambda: kms
    app.dependency_overrides[plaid_routes.get_connection_service] = lambda: connection_service
    app.dependency_overrides[plaid_routes.get_sync_jobs_repository] = lambda: sync_jobs_repo

    try:
        response = TestClient(app).delete(f"/api/v1/plaid/item/{connection_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert connection_service.calls == [
        {
            "db": db,
            "kms": kms,
            "sync_jobs_repo": sync_jobs_repo,
            "user_id": user_id,
            "connection_id": connection_id,
        }
    ]
    assert db.commits == 1
    assert db.rollbacks == 0


def test_revoke_item_rolls_back_when_service_raises():
    db = FakeTransactionalDb()
    connection_id = uuid4()
    error = ServiceUnavailableError(detail="Plaid unavailable")
    app.dependency_overrides[plaid_routes.get_db] = lambda: db
    app.dependency_overrides[plaid_routes.get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[plaid_routes.get_kms_service] = lambda: SimpleNamespace()
    app.dependency_overrides[plaid_routes.get_connection_service] = (
        lambda: RecordingConnectionService(error=error)
    )
    app.dependency_overrides[plaid_routes.get_sync_jobs_repository] = (
        lambda: RecordingSyncJobsRepo()
    )

    try:
        response = TestClient(app).delete(f"/api/v1/plaid/item/{connection_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Plaid unavailable"}
    assert db.commits == 0
    assert db.rollbacks == 1
