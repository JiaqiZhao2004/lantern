from sqlalchemy.orm import Session

from .items_service import PlaidItemsWebhookService
from .schema import PlaidWebhookPayload
from .transactions_service import PlaidTransactionsWebhookService


class PlaidWebhookService:
    def __init__(
        self,
        transactions_webhook_service: PlaidTransactionsWebhookService,
        items_webhook_service: PlaidItemsWebhookService,
    ):
        self.transactions_webhook_service = transactions_webhook_service
        self.items_webhook_service = items_webhook_service

    def dispatch(self, db: Session, payload: PlaidWebhookPayload):
        webhook_type = payload.webhook_type.upper()

        if webhook_type == "TRANSACTIONS":
            return self.transactions_webhook_service.handle(db=db, payload=payload)

        if webhook_type == "ITEM":
            return self.items_webhook_service.handle(db=db, payload=payload)

        return None
