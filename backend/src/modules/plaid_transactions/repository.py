from datetime import datetime
from datetime import timezone
from typing import Any

from sqlalchemy import and_, func, or_, update
from sqlalchemy.dialects.postgresql import insert

from ..accounts.models import Account
from ..institution_connections.models import InstitutionConnection
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

    def list_household_transactions(
        self,
        db: Session,
        *,
        household_id,
        account_ids: list,
        search: str | None,
        start_occurred_at: datetime | None,
        end_occurred_at_exclusive: datetime | None,
        order_by: str,
        order_direction: str,
        cursor_offset: int,
        limit: int,
    ):
        base_query = (
            db.query(
                Transaction.id.label("id"),
                Transaction.account_id.label("account_id"),
                Account.name.label("account_name"),
                InstitutionConnection.institution_name.label("institution_name"),
                Transaction.occurred_at.label("occurred_at"),
                Transaction.amount.label("amount"),
                Transaction.merchant_name.label("merchant_name"),
                Transaction.original_description.label("original_description"),
                Transaction.pending.label("pending"),
                Transaction.category_primary.label("category_primary"),
                Transaction.category_detailed.label("category_detailed"),
                Transaction.iso_currency_code.label("iso_currency_code"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .join(InstitutionConnection, Transaction.item_id == InstitutionConnection.id)
            .filter(
                Transaction.household_id == household_id,
                Transaction.is_removed.is_(False),
            )
        )

        if account_ids:
            base_query = base_query.filter(Transaction.account_id.in_(account_ids))

        if search:
            pattern = f"%{search}%"
            base_query = base_query.filter(
                or_(
                    Transaction.merchant_name.ilike(pattern),
                    Transaction.original_description.ilike(pattern),
                )
            )

        if start_occurred_at is not None:
            base_query = base_query.filter(Transaction.occurred_at >= start_occurred_at)

        if end_occurred_at_exclusive is not None:
            base_query = base_query.filter(
                Transaction.occurred_at < end_occurred_at_exclusive
            )

        total_count = base_query.order_by(None).count()
        ordered_columns = self._order_clauses(order_by, order_direction)
        numbered_query = base_query.add_columns(
            func.row_number().over(order_by=ordered_columns).label("row_num")
        )
        numbered_subquery = numbered_query.subquery()

        page_items = (
            db.query(numbered_subquery)
            .filter(numbered_subquery.c.row_num > cursor_offset)
            .order_by(numbered_subquery.c.row_num.asc())
            .limit(limit + 1)
            .all()
        )

        return total_count, page_items

    def _order_clauses(self, order_by: str, order_direction: str):
        order_column = {
            "date": Transaction.occurred_at,
            "merchant": Transaction.merchant_name,
            "account": Account.name,
            "category": Transaction.category_primary,
            "amount": Transaction.amount,
            "pending": Transaction.pending,
        }[order_by]
        directional_order = (
            order_column.asc() if order_direction == "asc" else order_column.desc()
        )
        tie_breaker = Transaction.id.asc() if order_direction == "asc" else Transaction.id.desc()
        return [directional_order.nullslast(), tie_breaker.nullslast()]
