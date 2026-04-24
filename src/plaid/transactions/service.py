import time
import json
from typing import Dict, Any
from .mapper import plaid_transaction_to_row
from .repository import TransactionRepository
from ..items.repository import PlaidItem, PlaidItemRepository
from ..accounts.mapper import plaid_accounts_to_rows
from ..accounts.repository import PlaidAccountRepository
from ...infrastructure import Session, PlaidClient, KMSService
import plaid
from plaid.model.transactions_sync_request import TransactionsSyncRequest


def transactions_sync(plaid_client: PlaidClient, cursor: str, access_token: str):
    accounts, added, modified, removed = [], [], [], []
    has_more = True
    try:
        while has_more:
            req = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
                options={"include_original_description": True},
            )
            resp = plaid_client.transactions_sync(req).to_dict()
            cursor = resp["next_cursor"]

            if cursor == "":
                time.sleep(2)
                continue

            accounts.extend(resp["accounts"])
            added.extend(resp["added"])
            modified.extend(resp["modified"])
            removed.extend(resp["removed"])
            has_more = resp["has_more"]
            print(resp)

        return {
            "accounts": accounts,
            "added": added,
            "modified": modified,
            "removed": removed,
            "next_cursor": cursor,
        }
    except plaid.ApiException as e:
        return format_error(e)


def format_error(e: plaid.ApiException) -> Dict[str, Any]:
    response = json.loads(str(e.body))
    return {
        "error": {
            "status_code": e.status,
            "display_message": response.get("error_message"),
            "error_code": response.get("error_code"),
            "error_type": response.get("error_type"),
        }
    }


class TransactionService:
    def __init__(
        self,
        plaid_item_repo: PlaidItemRepository,
        plaid_account_repo: PlaidAccountRepository,
        transaction_repo: TransactionRepository,
    ):
        self.plaid_item_repo = plaid_item_repo
        self.plaid_account_repo = plaid_account_repo
        self.transaction_repo = transaction_repo

    def sync(
        self,
        db: Session,
        kms: KMSService,
        plaid_client: PlaidClient,
        plaid_item: PlaidItem,
    ):
        cursor = plaid_item.transactions_cursor or ""
        access_token = kms.decrypt_secret(
            encrypted_data_key=plaid_item.access_token_encrypted_data_key,
            nonce=plaid_item.access_token_nonce,
            ciphertext=plaid_item.access_token_ciphertext,
        )
        sync_results = transactions_sync(plaid_client, cursor, access_token)
        accounts_updates = sync_results["accounts"]
        transactions_added = sync_results["added"]
        transactions_modified = sync_results["modified"]
        transactions_removed = sync_results["removed"]
        next_cursor = sync_results["next_cursor"]

        plaid_accounts = self.plaid_account_repo.upsert_many(
            db=db,
            item_id=plaid_item.id,
            account_rows=plaid_accounts_to_rows(accounts_updates),
        )
        plaid_accounts_by_id = {
            account.plaid_account_id: account for account in plaid_accounts
        }

        transaction_rows = [
            plaid_transaction_to_row(
                tx,
                account_id=plaid_accounts_by_id[tx["account_id"]].id,
                item_id=plaid_item.id,
                household_id=plaid_item.household_id,
            )
            for tx in transactions_added + transactions_modified
        ]

        self.transaction_repo.upsert_many(
            db=db,
            transaction_rows=transaction_rows,
        )

        self.transaction_repo.mark_removed_many(
            db=db,
            plaid_transaction_ids=[tx["transaction_id"] for tx in transactions_removed],
        )

        self.plaid_item_repo.update_cursor(
            db=db, plaid_item=plaid_item, cursor=next_cursor
        )
