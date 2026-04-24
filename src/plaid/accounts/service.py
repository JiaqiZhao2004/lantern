from uuid import UUID
from .mapper import plaid_accounts_to_rows
from ..accounts.repository import PlaidAccountRepository
from ..items.models import PlaidItem
from ...infrastructure import Session, KMSService, PlaidClient
from plaid.model.accounts_get_request import AccountsGetRequest


class PlaidAccountService:
    def __init__(
        self,
        plaid_account_repo: PlaidAccountRepository,
    ):
        self.plaid_account_repo = plaid_account_repo

    def sync_accounts_for_item(
        self, plaid_client: PlaidClient, item: PlaidItem, db: Session, kms: KMSService
    ) -> int:
        """
        Pull the latest account list from Plaid for *item* and upsert every
        account into the plaid_accounts table.

        Returns the number of accounts upserted.

        This is intentionally a plain function (not a route) so it can be called:
        - directly from add_item after the item is persisted, and
        - from the internal /internal/sync_accounts/{plaid_item_id} endpoint
            triggered by webhooks or schedulers.
        """
        # 1. Recover the plaintext access token via KMS envelope decryption
        access_token = kms.decrypt_secret(
            item.access_token_encrypted_data_key,
            item.access_token_nonce,
            item.access_token_ciphertext,
        )

        # 2. Call Plaid /accounts/get
        resp = plaid_client.accounts_get(AccountsGetRequest(access_token=access_token))
        accounts = resp["accounts"]

        # 3. Map Plaid's account shape into plaid_accounts columns
        account_rows = plaid_accounts_to_rows(accounts)

        # 4. Upsert each account
        self.plaid_account_repo.upsert_many(
            db=db,
            item_id=item.id,
            account_rows=account_rows,
        )

        return len(accounts)

    def list_household_accounts(self, db: Session, household_id: UUID):
        return self.plaid_account_repo.list_household_accounts(
            db=db, household_id=household_id
        )
