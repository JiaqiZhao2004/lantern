from src.plaid.webhooks.schema import PlaidWebhookPayload
from src.plaid.webhooks.service import PlaidWebhookService


class FakeProductWebhookService:
    def __init__(self):
        self.payloads = []

    def handle(self, db, payload):
        self.payloads.append(payload)
        return payload.webhook_code


def test_routes_transactions_webhooks_to_transactions_service():
    transactions_service = FakeProductWebhookService()
    items_service = FakeProductWebhookService()
    service = PlaidWebhookService(
        transactions_webhook_service=transactions_service,
        items_webhook_service=items_service,
    )

    result = service.dispatch(
        db=None,
        payload=PlaidWebhookPayload(
            webhook_type="TRANSACTIONS",
            webhook_code="SYNC_UPDATES_AVAILABLE",
        ),
    )

    assert result == "SYNC_UPDATES_AVAILABLE"
    assert len(transactions_service.payloads) == 1
    assert items_service.payloads == []


def test_routes_item_webhooks_to_items_service():
    transactions_service = FakeProductWebhookService()
    items_service = FakeProductWebhookService()
    service = PlaidWebhookService(
        transactions_webhook_service=transactions_service,
        items_webhook_service=items_service,
    )

    result = service.dispatch(
        db=None,
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="LOGIN_REPAIRED",
        ),
    )

    assert result == "LOGIN_REPAIRED"
    assert transactions_service.payloads == []
    assert len(items_service.payloads) == 1


def test_unknown_webhook_type_is_accepted_without_side_effects():
    transactions_service = FakeProductWebhookService()
    items_service = FakeProductWebhookService()
    service = PlaidWebhookService(
        transactions_webhook_service=transactions_service,
        items_webhook_service=items_service,
    )

    result = service.dispatch(
        db=None,
        payload=PlaidWebhookPayload(
            webhook_type="SOMETHING",
            webhook_code="NEW_EVENT",
        ),
    )

    assert result is None
    assert transactions_service.payloads == []
    assert items_service.payloads == []
