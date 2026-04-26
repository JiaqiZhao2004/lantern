from types import SimpleNamespace
from uuid import uuid4

from src.plaid.webhooks.schema import PlaidWebhookPayload
from src.plaid.webhooks.transactions_service import PlaidTransactionsWebhookService


class FakeSyncJobsRequestService:
    def __init__(self):
        self.webhook_item_ids = []

    def handle_webhook(self, db, plaid_item_id):
        self.webhook_item_ids.append(plaid_item_id)
        return SimpleNamespace(id=uuid4())


def test_sync_updates_available_enqueues_webhook_job():
    sync_request_service = FakeSyncJobsRequestService()
    service = PlaidTransactionsWebhookService(
        sync_jobs_request_service=sync_request_service
    )

    service.handle(
        db=None,
        payload=PlaidWebhookPayload(
            webhook_type="TRANSACTIONS",
            webhook_code="SYNC_UPDATES_AVAILABLE",
            item_id="item-1",
        ),
    )

    assert sync_request_service.webhook_item_ids == ["item-1"]


def test_legacy_transaction_webhook_is_ignored():
    sync_request_service = FakeSyncJobsRequestService()
    service = PlaidTransactionsWebhookService(
        sync_jobs_request_service=sync_request_service
    )

    service.handle(
        db=None,
        payload=PlaidWebhookPayload(
            webhook_type="TRANSACTIONS",
            webhook_code="DEFAULT_UPDATE",
            item_id="item-1",
        ),
    )

    assert sync_request_service.webhook_item_ids == []


def test_unknown_transaction_webhook_is_ignored():
    sync_request_service = FakeSyncJobsRequestService()
    service = PlaidTransactionsWebhookService(
        sync_jobs_request_service=sync_request_service
    )

    service.handle(
        db=None,
        payload=PlaidWebhookPayload(
            webhook_type="TRANSACTIONS",
            webhook_code="SOMETHING_NEW",
            item_id="item-1",
        ),
    )

    assert sync_request_service.webhook_item_ids == []
