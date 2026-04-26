from sqlalchemy.orm import Session

from src.exceptions import NotFoundError
from src.plaid.accounts.repository import PlaidAccountRepository
from src.plaid.items.repository import PlaidItemRepository
from src.sync.jobs.repository import SyncJobsRepository
from src.sync.jobs.request_service import SyncJobsRequestService

from .schema import PlaidWebhookPayload


class PlaidItemsWebhookService:
    def __init__(
        self,
        plaid_item_repo: PlaidItemRepository,
        plaid_account_repo: PlaidAccountRepository,
        sync_jobs_request_service: SyncJobsRequestService,
        sync_jobs_repo: SyncJobsRepository,
    ):
        self.plaid_item_repo = plaid_item_repo
        self.plaid_account_repo = plaid_account_repo
        self.sync_jobs_request_service = sync_jobs_request_service
        self.sync_jobs_repo = sync_jobs_repo

    def handle(self, db: Session, payload: PlaidWebhookPayload):
        webhook_code = payload.webhook_code.upper()

        if webhook_code == "ERROR":
            error_code = (payload.error or {}).get("error_code")
            if error_code == "ITEM_LOGIN_REQUIRED":
                return self._mark_needs_reauth(
                    db=db,
                    plaid_item_id=payload.item_id,
                    error="ITEM_LOGIN_REQUIRED",
                )
            return None

        if webhook_code == "LOGIN_REPAIRED":
            return self._handle_login_repaired(db=db, plaid_item_id=payload.item_id)

        if webhook_code in {"PENDING_DISCONNECT", "PENDING_EXPIRATION"}:
            return self._mark_needs_reauth(
                db=db,
                plaid_item_id=payload.item_id,
                error=webhook_code,
            )

        if webhook_code == "USER_PERMISSION_REVOKED":
            return self._mark_item_revoked(db=db, plaid_item_id=payload.item_id)

        if webhook_code == "USER_ACCOUNT_REVOKED":
            return self._mark_account_revoked(
                db=db,
                plaid_item_id=payload.item_id,
                plaid_account_id=payload.account_id,
            )

        if webhook_code in {"NEW_ACCOUNTS_AVAILABLE", "WEBHOOK_UPDATE_ACKNOWLEDGED"}:
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

    def _mark_needs_reauth(
        self,
        db: Session,
        plaid_item_id: str | None,
        error: str,
    ):
        if plaid_item_id is None:
            return None

        plaid_item = self.plaid_item_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if plaid_item is None:
            return None

        self.plaid_item_repo.mark_sync_needs_reauth(
            db=db,
            plaid_item=plaid_item,
            error=error,
        )
        self.sync_jobs_repo.cancel_queued_or_running_for_connection(
            db=db,
            institution_connection_id=plaid_item.id,
            last_error=error,
        )
        return plaid_item

    def _handle_login_repaired(self, db: Session, plaid_item_id: str | None):
        if plaid_item_id is None:
            return None

        plaid_item = self.plaid_item_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if plaid_item is None:
            return None

        self.plaid_item_repo.mark_item_active(db=db, plaid_item=plaid_item)
        self.plaid_item_repo.clear_sync_error(db=db, plaid_item=plaid_item)

        return self._enqueue_webhook_sync(db=db, plaid_item_id=plaid_item_id)

    def _mark_item_revoked(self, db: Session, plaid_item_id: str | None):
        if plaid_item_id is None:
            return None

        plaid_item = self.plaid_item_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if plaid_item is None:
            return None

        self.plaid_item_repo.mark_item_revoked_and_disabled(
            db=db,
            plaid_item=plaid_item,
            error="USER_PERMISSION_REVOKED",
        )
        self.sync_jobs_repo.cancel_queued_or_running_for_connection(
            db=db,
            institution_connection_id=plaid_item.id,
            last_error="USER_PERMISSION_REVOKED",
        )
        return plaid_item

    def _mark_account_revoked(
        self,
        db: Session,
        plaid_item_id: str | None,
        plaid_account_id: str | None,
    ):
        if plaid_item_id is None or plaid_account_id is None:
            return None

        plaid_item = self.plaid_item_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if plaid_item is None:
            return None

        return self.plaid_account_repo.mark_inactive_by_plaid_id(
            db=db,
            item_id=plaid_item.id,
            plaid_account_id=plaid_account_id,
        )
