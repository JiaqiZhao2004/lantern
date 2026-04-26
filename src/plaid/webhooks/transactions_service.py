from sqlalchemy.orm import Session

from src.exceptions import NotFoundError
from src.sync.jobs.request_service import SyncJobsRequestService

from .schema import PlaidWebhookPayload


class PlaidTransactionsWebhookService:
    LEGACY_TRANSACTION_CODES = {
        "INITIAL_UPDATE",
        "HISTORICAL_UPDATE",
        "DEFAULT_UPDATE",
        "TRANSACTIONS_REMOVED",
    }

    def __init__(self, sync_jobs_request_service: SyncJobsRequestService):
        self.sync_jobs_request_service = sync_jobs_request_service

    def handle(self, db: Session, payload: PlaidWebhookPayload):
        webhook_code = payload.webhook_code.upper()

        if webhook_code == "SYNC_UPDATES_AVAILABLE":
            return self._enqueue_webhook_sync(db=db, plaid_item_id=payload.item_id)

        if webhook_code in self.LEGACY_TRANSACTION_CODES:
            return None

        return None

    def _enqueue_webhook_sync(self, db: Session, plaid_item_id: str | None):
        if plaid_item_id is None:
            return None

        try:
            return self.sync_jobs_request_service.handle_webhook(
                db=db,
                plaid_item_id=plaid_item_id,
            )
        except NotFoundError:
            return None
