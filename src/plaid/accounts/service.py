from uuid import UUID
from datetime import datetime, timezone
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

        # 3. Upsert each account
        for acc in accounts:
            balances = acc.get("balances", {})
            plaid_account_id: str = acc["account_id"]

            last_balance_update_raw = balances.get("last_updated_datetime")
            last_balance_update_at: datetime | None = None
            if last_balance_update_raw is not None:
                if isinstance(last_balance_update_raw, datetime):
                    last_balance_update_at = last_balance_update_raw
                else:
                    last_balance_update_at = datetime.fromisoformat(
                        str(last_balance_update_raw)
                    )
                last_balance_update_at = last_balance_update_at.astimezone(timezone.utc)

            self.plaid_account_repo.create_or_update(
                db=db,
                plaid_item_id=item.plaid_item_id,
                plaid_account_id=plaid_account_id,
                mask=acc.get("mask"),
                name=acc.get("name"),
                official_name=acc.get("official_name"),
                account_type=str(acc["type"]) if acc.get("type") is not None else None,
                account_subtype=(
                    str(acc["subtype"]) if acc.get("subtype") is not None else None
                ),
                current_balance=balances.get("current"),
                available_balance=balances.get("available"),
                limit_amount=balances.get("limit"),
                iso_currency_code=balances.get("iso_currency_code"),
                unofficial_currency_code=balances.get("unofficial_currency_code"),
                last_balance_update_at=last_balance_update_at,
            )

        return len(accounts)

    def list_household_accounts(self, db: Session, household_id: UUID):
        return self.plaid_account_repo.list_household_accounts(
            db=db, household_id=household_id
        )
