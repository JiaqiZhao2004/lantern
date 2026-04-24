from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Any
from .models import PlaidAccount
from ..items.models import PlaidItem

_UNSET = object()


class PlaidAccountRepository:
    def get_by_id(
        self,
        db: Session,
        item_id: UUID,
        plaid_account_id: str,
    ):
        return (
            db.query(PlaidAccount)
            .filter_by(item_id=item_id, plaid_account_id=plaid_account_id)
            .first()
        )

    def upsert_one(
        self,
        db: Session,
        item_id: UUID,
        plaid_account_id: str,
        mask: str | None | object = _UNSET,
        name: str | None | object = _UNSET,
        official_name: str | None | object = _UNSET,
        account_type: str | None | object = _UNSET,
        account_subtype: str | None | object = _UNSET,
        current_balance: float | None | object = _UNSET,
        available_balance: float | None | object = _UNSET,
        limit_amount: float | None | object = _UNSET,
        iso_currency_code: str | None | object = _UNSET,
        unofficial_currency_code: str | None | object = _UNSET,
        owner_names: dict | None | object = _UNSET,
        is_active: bool | object = _UNSET,
        is_hidden: bool | object = _UNSET,
        display_order: int | None | object = _UNSET,
        last_balance_update_at: datetime | None | object = _UNSET,
    ) -> PlaidAccount:
        existing = self.get_by_id(
            db=db, item_id=item_id, plaid_account_id=plaid_account_id
        )

        fields = dict(
            mask=mask,
            name=name,
            official_name=official_name,
            account_type=account_type,
            account_subtype=account_subtype,
            current_balance=current_balance,
            available_balance=available_balance,
            limit_amount=limit_amount,
            iso_currency_code=iso_currency_code,
            unofficial_currency_code=unofficial_currency_code,
            owner_names=owner_names,
            is_active=is_active,
            is_hidden=is_hidden,
            display_order=display_order,
            last_balance_update_at=last_balance_update_at,
        )
        fields = {k: v for k, v in fields.items() if v is not _UNSET}

        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)

        else:
            account = PlaidAccount(
                item_id=item_id,
                plaid_account_id=plaid_account_id,
                **fields,
            )
            db.add(account)

        db.flush()
        return existing if existing else account

    def upsert_many(
        self,
        db: Session,
        item_id: UUID,
        account_rows: list[dict[str, Any]],
    ) -> list[PlaidAccount]:
        if not account_rows:
            return []

        plaid_account_ids = [row["plaid_account_id"] for row in account_rows]
        existing_accounts = (
            db.query(PlaidAccount)
            .filter(
                PlaidAccount.item_id == item_id,
                PlaidAccount.plaid_account_id.in_(plaid_account_ids),
            )
            .all()
        )
        existing_by_plaid_id = {
            account.plaid_account_id: account for account in existing_accounts
        }

        upserted_accounts: list[PlaidAccount] = []
        for row in account_rows:
            plaid_account_id = row["plaid_account_id"]
            fields = {
                key: value for key, value in row.items() if key != "plaid_account_id"
            }
            existing = existing_by_plaid_id.get(plaid_account_id)

            if existing:
                for key, value in fields.items():
                    setattr(existing, key, value)
                upserted_accounts.append(existing)
                continue

            account = PlaidAccount(
                item_id=item_id,
                plaid_account_id=plaid_account_id,
                **fields,
            )
            db.add(account)
            upserted_accounts.append(account)

        db.flush()
        return upserted_accounts

    def list_household_accounts(self, db: Session, household_id: UUID):
        return (
            db.query(PlaidAccount)
            .join(PlaidAccount.item)
            .filter(PlaidItem.household_id == household_id)
            .order_by(PlaidItem.created_at, PlaidAccount.created_at)
            .all()
        )
