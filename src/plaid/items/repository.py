from sqlalchemy.orm import Session
from datetime import datetime, timezone
from uuid import UUID
from .models import PlaidItem, PlaidItemSyncState, PlaidItemStatus
from ...app.user.models import User
from ...infrastructure.aws.kms import KMSService


class PlaidItemRepository:

    def create_encrypted(
        self,
        db: Session,
        kms: KMSService,
        user: User,
        household_id: UUID,
        plaid_item_id: str,
        plaid_access_token: str,
        institution_id: str | None,
        institution_name: str | None,
    ):
        ciphertext, nonce, encrypted_data_key = kms.encrypt_secret(plaid_access_token)
        item = PlaidItem(
            user_id=user.id,
            household_id=household_id,
            plaid_item_id=plaid_item_id,
            institution_id=institution_id,
            institution_name=institution_name,
            access_token_ciphertext=ciphertext,
            access_token_nonce=nonce,
            access_token_encrypted_data_key=encrypted_data_key,
        )
        db.add(item)
        db.flush()  # ensures item.id is available before commit
        return item

    def list_household_items(self, db: Session, household_id: UUID):
        return (
            db.query(PlaidItem)
            .filter(PlaidItem.household_id == household_id)
            .order_by(PlaidItem.created_at)
            .all()
        )

    def get_by_plaid_item_id(self, db: Session, plaid_item_id: str):
        return (
            db.query(PlaidItem).filter(PlaidItem.plaid_item_id == plaid_item_id).first()
        )

    # needs_resync
    def mark_need_resync(self, db: Session, plaid_item: PlaidItem):
        plaid_item.needs_resync = True
        db.flush()
        return plaid_item

    def clear_need_resync(self, db: Session, plaid_item: PlaidItem):
        plaid_item.needs_resync = False
        db.flush()
        return plaid_item

    # sync state
    def is_syncing(self, plaid_item: PlaidItem):
        return plaid_item.sync_state == PlaidItemSyncState.SYNCING

    def is_waiting_for_retry(self, plaid_item: PlaidItem):
        return plaid_item.sync_state == PlaidItemSyncState.RETRY_SCHEDULED

    def is_unable_to_sync(self, plaid_item: PlaidItem):
        return (
            plaid_item.sync_state == PlaidItemSyncState.DISABLED
            or plaid_item.sync_state == PlaidItemSyncState.NEEDS_REAUTH
        )

    def mark_syncing(self, db: Session, plaid_item: PlaidItem):
        plaid_item.sync_state = PlaidItemSyncState.SYNCING
        db.flush()
        return plaid_item

    def mark_in_sync(self, db: Session, plaid_item: PlaidItem):
        plaid_item.sync_state = PlaidItemSyncState.IN_SYNC
        plaid_item.last_synced_at = datetime.now(timezone.utc)
        db.flush()
        return plaid_item

    def mark_sync_retry_scheduled(self, db: Session, plaid_item: PlaidItem, error: str):
        plaid_item.sync_state = PlaidItemSyncState.RETRY_SCHEDULED
        plaid_item.last_sync_error = error
        db.flush()
        return plaid_item

    def mark_sync_needs_reauth(
        self, db: Session, plaid_item: PlaidItem, error: str = "Needs reauthentication"
    ):
        plaid_item.sync_state = PlaidItemSyncState.NEEDS_REAUTH
        plaid_item.last_sync_error = error
        db.flush()
        return plaid_item

    def mark_sync_disabled(self, db: Session, plaid_item: PlaidItem, error: str):
        plaid_item.sync_state = PlaidItemSyncState.DISABLED
        plaid_item.last_sync_error = error
        db.flush()
        return plaid_item

    # status
    def is_active(self, plaid_item: PlaidItem):
        return plaid_item.status == PlaidItemStatus.ACTIVE

    def mark_item_revoked(self, db: Session, plaid_item: PlaidItem):
        plaid_item.status = PlaidItemStatus.REVOKED
        db.flush()
        return plaid_item

    def mark_item_active(self, db: Session, plaid_item: PlaidItem):
        plaid_item.status = PlaidItemStatus.ACTIVE
        db.flush()
        return plaid_item

    # cursor
    def update_cursor(self, db: Session, plaid_item: PlaidItem, cursor: str):
        plaid_item.transactions_cursor = cursor
        db.flush()
        return plaid_item
