from sqlalchemy.orm import Session

from src.exceptions import NotFoundError
from src.modules.accounts.repository import AccountRepository
from src.modules.institution_connections.repository import InstitutionConnectionRepository
from src.modules.sync_jobs.repository import SyncJobsRepository
from src.modules.sync_jobs.request_service import SyncJobsRequestService

from .schema import PlaidWebhookPayload


class PlaidItemsWebhookService:
    def __init__(
        self,
        connection_repo: InstitutionConnectionRepository,
        account_repo: AccountRepository,
        sync_jobs_request_service: SyncJobsRequestService,
        sync_jobs_repo: SyncJobsRepository,
    ):
        self.connection_repo = connection_repo
        self.account_repo = account_repo
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
            return self.sync_jobs_request_service.create_webhook_sync_job(
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

        connection = self.connection_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if connection is None:
            return None

        self.connection_repo.mark_sync_needs_reauth(
            db=db,
            connection=connection,
            error=error,
        )
        self.sync_jobs_repo.cancel_queued_or_running_for_connection(
            db=db,
            institution_connection_id=connection.id,
            last_error=error,
        )
        return connection

    def _handle_login_repaired(self, db: Session, plaid_item_id: str | None):
        if plaid_item_id is None:
            return None

        connection = self.connection_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if connection is None:
            return None

        self.connection_repo.mark_active(db=db, connection=connection)
        self.connection_repo.clear_sync_error(db=db, connection=connection)

        return self._enqueue_webhook_sync(db=db, plaid_item_id=plaid_item_id)

    def _mark_item_revoked(self, db: Session, plaid_item_id: str | None):
        if plaid_item_id is None:
            return None

        connection = self.connection_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if connection is None:
            return None

        self.connection_repo.mark_revoked_and_disabled(
            db=db,
            connection=connection,
            error="USER_PERMISSION_REVOKED",
        )
        self.sync_jobs_repo.cancel_queued_or_running_for_connection(
            db=db,
            institution_connection_id=connection.id,
            last_error="USER_PERMISSION_REVOKED",
        )
        return connection

    def _mark_account_revoked(
        self,
        db: Session,
        plaid_item_id: str | None,
        plaid_account_id: str | None,
    ):
        if plaid_item_id is None or plaid_account_id is None:
            return None

        connection = self.connection_repo.get_by_plaid_item_id(
            db=db,
            plaid_item_id=plaid_item_id,
        )
        if connection is None:
            return None

        return self.account_repo.mark_inactive_by_plaid_id(
            db=db,
            institution_connection_id=connection.id,
            plaid_account_id=plaid_account_id,
        )
