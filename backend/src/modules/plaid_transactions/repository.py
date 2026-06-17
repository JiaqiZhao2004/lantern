from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update
from datetime import datetime
from datetime import timezone
from typing import Any
from .models import Transaction
from ...infrastructure import Session


class TransactionRepository:
    def upsert_many(
        self,
        db: Session,
        transaction_rows: list[dict[str, Any]],
    ):
        if not transaction_rows:
            return

        stmt = insert(Transaction).values(transaction_rows)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[Transaction.plaid_transaction_id],
            index_where=Transaction.is_removed.is_(False),
            set_={
                "account_id": stmt.excluded.account_id,
                "item_id": stmt.excluded.item_id,
                "household_id": stmt.excluded.household_id,
                "is_removed": stmt.excluded.is_removed,
                "pending": stmt.excluded.pending,
                "amount": stmt.excluded.amount,
                "authorized_date": stmt.excluded.authorized_date,
                "posted_date": stmt.excluded.posted_date,
                "occurred_at": stmt.excluded.occurred_at,
                "merchant_name": stmt.excluded.merchant_name,
                "category_primary": stmt.excluded.category_primary,
                "category_detailed": stmt.excluded.category_detailed,
                "iso_currency_code": stmt.excluded.iso_currency_code,
                "pending_transaction_id": stmt.excluded.pending_transaction_id,
                "payment_channel": stmt.excluded.payment_channel,
                "check_number": stmt.excluded.check_number,
                "original_description": stmt.excluded.original_description,
                "interbank_transfer_info": stmt.excluded.interbank_transfer_info,
                "logo_url": stmt.excluded.logo_url,
                "updated_at": datetime.now(timezone.utc),
                "removed_at": None,
            },
        )

        db.execute(upsert_stmt)
        db.flush()

    def mark_removed_many(self, db: Session, plaid_transaction_ids: list[str]):
        if not plaid_transaction_ids:
            return

        now = datetime.now(timezone.utc)

        stmt = (
            update(Transaction)
            .where(
                Transaction.plaid_transaction_id.in_(plaid_transaction_ids),
                Transaction.is_removed.is_(False),
            )
            .values(
                is_removed=True,
                removed_at=now,
                updated_at=now,
            )
        )

        db.execute(stmt)
        db.flush()
