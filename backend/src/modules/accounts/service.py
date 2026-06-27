from uuid import UUID
from .mapper import plaid_accounts_to_rows
from .repository import AccountRepository
from ..institution_connections.models import InstitutionConnection
from ...infrastructure import Session, KMSService, PlaidClient
from ...exceptions import NotFoundError
from plaid.model.accounts_get_request import AccountsGetRequest


class AccountService:
    def __init__(
        self,
        account_repo: AccountRepository,
    ):
        self.account_repo = account_repo

    def sync_accounts_for_connection(
        self, plaid_client: PlaidClient, connection: InstitutionConnection, db: Session, kms: KMSService
    ) -> int:
        access_token = kms.decrypt_secret(
            connection.plaid_access_token_encrypted_data_key,
            connection.plaid_access_token_nonce,
            connection.plaid_access_token_ciphertext,
        )

        resp = plaid_client.accounts_get(AccountsGetRequest(access_token=access_token))
        accounts = resp["accounts"]

        account_rows = plaid_accounts_to_rows(accounts)

        self.account_repo.upsert_many(
            db=db,
            institution_connection_id=connection.id,
            account_rows=account_rows,
        )

        return len(accounts)

    def list_household_accounts(self, db: Session, household_id: UUID):
        return self.account_repo.list_household_accounts(
            db=db, household_id=household_id
        )

    def set_query_tracking_enabled(
        self,
        db: Session,
        *,
        household_id: UUID,
        account_id: UUID,
        is_query_tracking_enabled: bool,
    ):
        account = self.account_repo.get_household_account(
            db=db,
            household_id=household_id,
            account_id=account_id,
        )
        if account is None:
            raise NotFoundError(detail="Account not found")

        return self.account_repo.set_query_tracking_enabled(
            db=db,
            account=account,
            is_query_tracking_enabled=is_query_tracking_enabled,
        )
