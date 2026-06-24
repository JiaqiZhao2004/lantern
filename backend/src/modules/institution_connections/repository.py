from sqlalchemy.orm import Session
from datetime import datetime, timezone
from uuid import UUID
from .models import InstitutionConnection, InstitutionConnectionSyncState, InstitutionConnectionStatus
from ..user.models import User
from ...infrastructure.aws.kms import KMSService


class InstitutionConnectionRepository:

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
        connection = InstitutionConnection(
            user_id=user.id,
            household_id=household_id,
            plaid_item_id=plaid_item_id,
            institution_id=institution_id,
            institution_name=institution_name,
            plaid_access_token_ciphertext=ciphertext,
            plaid_access_token_nonce=nonce,
            plaid_access_token_encrypted_data_key=encrypted_data_key,
        )
        db.add(connection)
        db.flush()
        return connection

    def list_household_connections(self, db: Session, household_id: UUID):
        return (
            db.query(InstitutionConnection)
            .filter(InstitutionConnection.household_id == household_id)
            .order_by(InstitutionConnection.created_at)
            .all()
        )

    def list_active(self, db: Session):
        return (
            db.query(InstitutionConnection)
            .filter(InstitutionConnection.status == InstitutionConnectionStatus.ACTIVE)
            .order_by(InstitutionConnection.created_at)
            .all()
        )

    def get_by_plaid_item_id(self, db: Session, plaid_item_id: str):
        return (
            db.query(InstitutionConnection)
            .filter(InstitutionConnection.plaid_item_id == plaid_item_id)
            .first()
        )

    def mark_need_resync(self, db: Session, connection: InstitutionConnection):
        connection.needs_resync = True
        db.flush()
        return connection

    def clear_need_resync(self, db: Session, connection: InstitutionConnection):
        connection.needs_resync = False
        db.flush()
        return connection

    def is_syncing(self, connection: InstitutionConnection):
        return connection.sync_state == InstitutionConnectionSyncState.SYNCING

    def is_waiting_for_retry(self, connection: InstitutionConnection):
        return connection.sync_state == InstitutionConnectionSyncState.RETRY_SCHEDULED

    def is_unable_to_sync(self, connection: InstitutionConnection):
        return (
            connection.sync_state == InstitutionConnectionSyncState.DISABLED
            or connection.sync_state == InstitutionConnectionSyncState.NEEDS_REAUTH
        )

    def mark_syncing(self, db: Session, connection: InstitutionConnection):
        connection.sync_state = InstitutionConnectionSyncState.SYNCING
        db.flush()
        return connection

    def mark_in_sync(self, db: Session, connection: InstitutionConnection):
        connection.sync_state = InstitutionConnectionSyncState.IN_SYNC
        connection.last_synced_at = datetime.now(timezone.utc)
        connection.last_sync_error = None
        db.flush()
        return connection

    def clear_sync_error(self, db: Session, connection: InstitutionConnection):
        connection.sync_state = InstitutionConnectionSyncState.IN_SYNC
        connection.last_sync_error = None
        connection.needs_resync = False
        db.flush()
        return connection

    def mark_sync_retry_scheduled(self, db: Session, connection: InstitutionConnection, error: str):
        connection.sync_state = InstitutionConnectionSyncState.RETRY_SCHEDULED
        connection.last_sync_error = error
        db.flush()
        return connection

    def mark_sync_needs_reauth(
        self, db: Session, connection: InstitutionConnection, error: str = "Needs reauthentication"
    ):
        connection.sync_state = InstitutionConnectionSyncState.NEEDS_REAUTH
        connection.last_sync_error = error
        db.flush()
        return connection

    def mark_sync_disabled(self, db: Session, connection: InstitutionConnection, error: str):
        connection.sync_state = InstitutionConnectionSyncState.DISABLED
        connection.last_sync_error = error
        db.flush()
        return connection

    def is_active(self, connection: InstitutionConnection):
        return connection.status == InstitutionConnectionStatus.ACTIVE

    def mark_revoked(self, db: Session, connection: InstitutionConnection):
        connection.status = InstitutionConnectionStatus.REVOKED
        db.flush()
        return connection

    def mark_revoked_and_disabled(
        self, db: Session, connection: InstitutionConnection, error: str
    ):
        connection.status = InstitutionConnectionStatus.REVOKED
        connection.sync_state = InstitutionConnectionSyncState.DISABLED
        connection.needs_resync = False
        connection.last_sync_error = error
        db.flush()
        return connection

    def mark_active(self, db: Session, connection: InstitutionConnection):
        connection.status = InstitutionConnectionStatus.ACTIVE
        db.flush()
        return connection

    def mark_member_departed(self, db: Session, connection: InstitutionConnection):
        connection.status = InstitutionConnectionStatus.MEMBER_DEPARTED
        connection.sync_state = InstitutionConnectionSyncState.DISABLED
        connection.needs_resync = False
        db.flush()
        return connection

    def update_cursor(self, db: Session, connection: InstitutionConnection, cursor: str):
        connection.transactions_cursor = cursor
        db.flush()
        return connection
