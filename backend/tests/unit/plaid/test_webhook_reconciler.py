from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.modules.institution_connections.plaid_webhook_reconciler import (
    PlaidWebhookReconciler,
)


class FakeConnectionRepo:
    def __init__(self, connections):
        self.connections = connections

    def list_active(self, db):
        return self.connections


class FakeKms:
    def __init__(self):
        self.decrypt_calls = []

    def decrypt_secret(self, encrypted_data_key, nonce, ciphertext):
        self.decrypt_calls.append((encrypted_data_key, nonce, ciphertext))
        return f"access-token-{len(self.decrypt_calls)}"


class FakePlaidClient:
    def __init__(self, webhooks, error=None):
        self.webhooks = list(webhooks)
        self.error = error
        self.item_get_requests = []
        self.item_webhook_update_requests = []

    def item_get(self, request):
        if self.error is not None:
            raise self.error
        self.item_get_requests.append(request)
        webhook = self.webhooks.pop(0)
        return {"item": {"webhook": webhook}}

    def item_webhook_update(self, request):
        self.item_webhook_update_requests.append(request)
        return {"item": {"webhook": request.to_dict()["webhook"]}}


def _connection(plaid_item_id="item-1"):
    return SimpleNamespace(
        id=uuid4(),
        plaid_item_id=plaid_item_id,
        plaid_access_token_encrypted_data_key=b"key",
        plaid_access_token_nonce=b"nonce",
        plaid_access_token_ciphertext=b"ciphertext",
    )


def test_dry_run_counts_active_connections_without_external_calls():
    kms = FakeKms()
    plaid_client = FakePlaidClient(webhooks=[])
    reconciler = PlaidWebhookReconciler(
        connection_repo=FakeConnectionRepo([_connection(), _connection()]),
        kms=kms,
        plaid_client=plaid_client,
        webhook_url=None,
    )

    result = reconciler.dry_run(db=object())

    assert result.checked == 2
    assert result.updated == 0
    assert result.skipped == 2
    assert kms.decrypt_calls == []
    assert plaid_client.item_get_requests == []
    assert plaid_client.item_webhook_update_requests == []


def test_apply_fails_fast_when_webhook_url_is_empty():
    kms = FakeKms()
    plaid_client = FakePlaidClient(webhooks=[])
    reconciler = PlaidWebhookReconciler(
        connection_repo=FakeConnectionRepo([_connection()]),
        kms=kms,
        plaid_client=plaid_client,
        webhook_url="",
    )

    with pytest.raises(ValueError, match="PLAID_WEBHOOK_URL"):
        reconciler.apply(db=object())

    assert kms.decrypt_calls == []
    assert plaid_client.item_get_requests == []


def test_apply_updates_only_missing_or_stale_webhooks():
    desired_webhook = "https://lantern.royzhao.dev/api/v1/plaid/webhooks"
    kms = FakeKms()
    plaid_client = FakePlaidClient(
        webhooks=[
            desired_webhook,
            None,
            "https://old.example.com/api/v1/plaid/webhooks",
        ]
    )
    reconciler = PlaidWebhookReconciler(
        connection_repo=FakeConnectionRepo(
            [
                _connection("item-current"),
                _connection("item-missing"),
                _connection("item-stale"),
            ]
        ),
        kms=kms,
        plaid_client=plaid_client,
        webhook_url=desired_webhook,
    )

    result = reconciler.apply(db=object())

    assert result.checked == 3
    assert result.updated == 2
    assert result.skipped == 1
    assert len(kms.decrypt_calls) == 3
    assert len(plaid_client.item_get_requests) == 3
    assert len(plaid_client.item_webhook_update_requests) == 2
    assert [
        request.to_dict()["webhook"]
        for request in plaid_client.item_webhook_update_requests
    ] == [desired_webhook, desired_webhook]


def test_apply_succeeds_when_no_active_connections_exist():
    reconciler = PlaidWebhookReconciler(
        connection_repo=FakeConnectionRepo([]),
        kms=FakeKms(),
        plaid_client=FakePlaidClient(webhooks=[]),
        webhook_url="https://lantern.royzhao.dev/api/v1/plaid/webhooks",
    )

    result = reconciler.apply(db=object())

    assert result.checked == 0
    assert result.updated == 0
    assert result.skipped == 0


def test_apply_propagates_plaid_failures():
    reconciler = PlaidWebhookReconciler(
        connection_repo=FakeConnectionRepo([_connection()]),
        kms=FakeKms(),
        plaid_client=FakePlaidClient(webhooks=[], error=RuntimeError("plaid down")),
        webhook_url="https://lantern.royzhao.dev/api/v1/plaid/webhooks",
    )

    with pytest.raises(RuntimeError, match="plaid down"):
        reconciler.apply(db=object())
