import time
import json
import logging
from typing import Dict, Any
from .mapper import plaid_transaction_to_row
from .repository import TransactionRepository
from ..institution_connections.repository import InstitutionConnection, InstitutionConnectionRepository
from ..accounts.mapper import plaid_accounts_to_rows
from ..accounts.repository import AccountRepository
from ...infrastructure import Session, PlaidClient, KMSService
from ...exceptions import InternalError
import plaid
from plaid.model.transactions_sync_request import TransactionsSyncRequest


logger = logging.getLogger(__name__)


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
        logger.exception("Failed to sync Plaid transactions")
        raise InternalError() from e


class TransactionService:
    def __init__(
        self,
        connection_repo: InstitutionConnectionRepository,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
    ):
        self.connection_repo = connection_repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    def sync(
        self,
        db: Session,
        kms: KMSService,
        plaid_client: PlaidClient,
        connection: InstitutionConnection,
    ):
        cursor = connection.transactions_cursor or ""
        access_token = kms.decrypt_secret(
            encrypted_data_key=connection.plaid_access_token_encrypted_data_key,
            nonce=connection.plaid_access_token_nonce,
            ciphertext=connection.plaid_access_token_ciphertext,
        )
        sync_results = transactions_sync(plaid_client, cursor, access_token)
        accounts_updates = sync_results["accounts"]
        transactions_added = sync_results["added"]
        transactions_modified = sync_results["modified"]
        transactions_removed = sync_results["removed"]
        next_cursor = sync_results["next_cursor"]

        accounts = self.account_repo.upsert_many(
            db=db,
            institution_connection_id=connection.id,
            account_rows=plaid_accounts_to_rows(accounts_updates),
        )
        accounts_by_plaid_id = {
            account.plaid_account_id: account for account in accounts
        }

        transaction_rows = [
            plaid_transaction_to_row(
                tx,
                account_id=accounts_by_plaid_id[tx["account_id"]].id,
                item_id=connection.id,
                household_id=connection.household_id,
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

        self.connection_repo.update_cursor(
            db=db, connection=connection, cursor=next_cursor
        )
