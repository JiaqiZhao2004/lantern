import json
import logging
import time
from datetime import UTC, date, datetime, time as day_time, timedelta
from typing import Any, Dict
from uuid import UUID

import base64
import plaid
from .mapper import plaid_transaction_to_row
from .repository import TransactionRepository
from ..accounts.repository import AccountRepository
from ..accounts.mapper import plaid_accounts_to_rows
from ..institution_connections.repository import InstitutionConnection, InstitutionConnectionRepository
from ...infrastructure import Session, PlaidClient, KMSService
from ...exceptions import InternalError, ValidationError
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from .schema import (
    TransactionLedgerFiltersDTO,
    TransactionLedgerItemDTO,
    TransactionLedgerPageInfoDTO,
    TransactionLedgerResponseDTO,
)


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


class TransactionLedgerService:
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo

    def list_for_household(
        self,
        db: Session,
        *,
        household_id: UUID,
        filters: TransactionLedgerFiltersDTO,
    ) -> TransactionLedgerResponseDTO:
        search = filters.search.strip() if filters.search else None
        if search == "":
            search = None

        if filters.start_date and filters.end_date and filters.start_date > filters.end_date:
            raise ValidationError(detail="start_date must be on or before end_date")

        cursor_occurred_at, cursor_transaction_id = self._decode_cursor(filters.cursor)

        total_count, rows = self.transaction_repo.list_household_transactions(
            db=db,
            household_id=household_id,
            account_ids=filters.account_ids,
            search=search,
            start_occurred_at=self._start_of_day(filters.start_date),
            end_occurred_at_exclusive=self._end_of_day_exclusive(filters.end_date),
            cursor_occurred_at=cursor_occurred_at,
            cursor_transaction_id=cursor_transaction_id,
            limit=filters.limit,
        )

        has_next_page = len(rows) > filters.limit
        visible_rows = rows[: filters.limit]
        next_cursor = None

        if has_next_page and visible_rows:
            last_row = visible_rows[-1]
            next_cursor = self._encode_cursor(
                occurred_at=last_row.occurred_at,
                transaction_id=last_row.id,
            )

        return TransactionLedgerResponseDTO(
            items=[
                TransactionLedgerItemDTO(
                    id=row.id,
                    account_id=row.account_id,
                    account_name=row.account_name,
                    institution_name=row.institution_name,
                    occurred_at=row.occurred_at,
                    amount=row.amount,
                    merchant_name=row.merchant_name,
                    original_description=row.original_description,
                    pending=row.pending,
                    category_primary=row.category_primary,
                    category_detailed=row.category_detailed,
                    iso_currency_code=row.iso_currency_code,
                )
                for row in visible_rows
            ],
            page=TransactionLedgerPageInfoDTO(
                next_cursor=next_cursor,
                has_next_page=has_next_page,
                total_count=total_count,
                limit=filters.limit,
            ),
        )

    def _encode_cursor(self, *, occurred_at: datetime, transaction_id: UUID) -> str:
        payload = {
            "occurred_at": occurred_at.astimezone(UTC).isoformat(),
            "id": str(transaction_id),
        }
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        return encoded.rstrip("=")

    def _decode_cursor(self, cursor: str | None) -> tuple[datetime | None, UUID | None]:
        if cursor is None:
            return None, None

        try:
            padding = "=" * (-len(cursor) % 4)
            payload = json.loads(
                base64.urlsafe_b64decode(f"{cursor}{padding}".encode("utf-8")).decode("utf-8")
            )
            occurred_at = datetime.fromisoformat(payload["occurred_at"])
            transaction_id = UUID(payload["id"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            raise ValidationError(detail="Invalid cursor")

        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        return occurred_at, transaction_id

    def _start_of_day(self, value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value, day_time.min, tzinfo=UTC)

    def _end_of_day_exclusive(self, value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value + timedelta(days=1), day_time.min, tzinfo=UTC)
