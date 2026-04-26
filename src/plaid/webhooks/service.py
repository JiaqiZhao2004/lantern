from sqlalchemy.orm import Session

from .schema import PlaidWebhookPayload
from .transactions_service import PlaidTransactionsWebhookService


class PlaidWebhookService:
    def __init__(
        self,
        transactions_webhook_service: PlaidTransactionsWebhookService,
    ):
        self.transactions_webhook_service = transactions_webhook_service

    def dispatch(self, db: Session, payload: PlaidWebhookPayload):
        webhook_type = payload.webhook_type.upper()

        if webhook_type == "TRANSACTIONS":
            return self.transactions_webhook_service.handle(db=db, payload=payload)

        return None
