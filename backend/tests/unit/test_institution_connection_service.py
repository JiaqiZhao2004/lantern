from types import SimpleNamespace
from uuid import uuid4

import pytest
import plaid

from src.exceptions import InternalError, NotFoundError
from src.modules.institution_connections.service import InstitutionConnectionService


class FakeConnectionRepo:
    def __init__(self, connection):
        self.connection = connection
        self.deleted = []
        self.requests = []

    def get_by_id_for_user(self, db, connection_id, user_id):
        self.requests.append((db, connection_id, user_id))
        if self.connection and self.connection.id == connection_id and self.connection.user_id == user_id:
            return self.connection
        return None

    def delete(self, db, connection):
        self.deleted.append((db, connection))


class FakeMembershipRepo:
    pass


class FakeKms:
    def __init__(self, plaintext):
        self.plaintext = plaintext
        self.calls = []

    def decrypt_secret(self, encrypted_data_key, nonce, ciphertext):
        self.calls.append((encrypted_data_key, nonce, ciphertext))
        return self.plaintext


class FakePlaidClient:
    def __init__(self, error=None):
        self.error = error
        self.requests = []

    def item_remove(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return {"removed": True}


class FakeSyncJobsRepo:
    def __init__(self):
        self.cancelled = []

    def cancel_queued_or_running_for_connection(
        self, db, institution_connection_id, last_error=None
    ):
        self.cancelled.append((db, institution_connection_id, last_error))


def _make_service(connection, plaid_client=None):
    connection_repo = FakeConnectionRepo(connection)
    service = InstitutionConnectionService(
        connection_repo=connection_repo,
        membership_repo=FakeMembershipRepo(),
        plaid_client=plaid_client or FakePlaidClient(),
    )
    return service, connection_repo


def test_revoke_connection_removes_remote_access_cancels_jobs_and_deletes_connection():
    db = object()
    user_id = uuid4()
    connection = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        plaid_access_token_encrypted_data_key=b"key",
        plaid_access_token_nonce=b"nonce",
        plaid_access_token_ciphertext=b"ciphertext",
    )
    plaid_client = FakePlaidClient()
    kms = FakeKms("access-sandbox-token")
    sync_jobs_repo = FakeSyncJobsRepo()
    service, connection_repo = _make_service(connection, plaid_client=plaid_client)

    service.revoke_connection(
        db=db,
        kms=kms,
        sync_jobs_repo=sync_jobs_repo,
        user_id=user_id,
        connection_id=connection.id,
    )

    assert len(plaid_client.requests) == 1
    assert kms.calls == [(b"key", b"nonce", b"ciphertext")]
    assert sync_jobs_repo.cancelled == [
        (db, connection.id, "User revoked institution connection")
    ]
    assert connection_repo.deleted == [(db, connection)]


def test_revoke_connection_raises_not_found_for_other_users():
    user_id = uuid4()
    connection = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        plaid_access_token_encrypted_data_key=b"key",
        plaid_access_token_nonce=b"nonce",
        plaid_access_token_ciphertext=b"ciphertext",
    )
    service, _ = _make_service(connection)

    with pytest.raises(NotFoundError, match="Institution connection not found"):
        service.revoke_connection(
            db=object(),
            kms=FakeKms("access-sandbox-token"),
            sync_jobs_repo=FakeSyncJobsRepo(),
            user_id=user_id,
            connection_id=connection.id,
        )


def test_revoke_connection_raises_internal_error_when_plaid_remove_fails():
    db = object()
    user_id = uuid4()
    connection = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        plaid_access_token_encrypted_data_key=b"key",
        plaid_access_token_nonce=b"nonce",
        plaid_access_token_ciphertext=b"ciphertext",
    )
    plaid_client = FakePlaidClient(error=plaid.ApiException(reason="boom"))
    service, connection_repo = _make_service(connection, plaid_client=plaid_client)

    with pytest.raises(InternalError, match="Unable to revoke institution connection"):
        service.revoke_connection(
            db=db,
            kms=FakeKms("access-sandbox-token"),
            sync_jobs_repo=FakeSyncJobsRepo(),
            user_id=user_id,
            connection_id=connection.id,
        )

    assert connection_repo.deleted == []
