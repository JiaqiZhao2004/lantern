from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Any
from .models import Account
from ..institution_connections.models import InstitutionConnection

_UNSET = object()


class AccountRepository:
    def get_by_id(
        self,
        db: Session,
        institution_connection_id: UUID,
        plaid_account_id: str,
    ):
        return (
            db.query(Account)
            .filter_by(institution_connection_id=institution_connection_id, plaid_account_id=plaid_account_id)
            .first()
        )

    def upsert_one(
        self,
        db: Session,
        institution_connection_id: UUID,
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
        is_query_tracking_enabled: bool | object = _UNSET,
        display_order: int | None | object = _UNSET,
        last_balance_update_at: datetime | None | object = _UNSET,
    ) -> Account:
        existing = self.get_by_id(
            db=db, institution_connection_id=institution_connection_id, plaid_account_id=plaid_account_id
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
            is_query_tracking_enabled=is_query_tracking_enabled,
            display_order=display_order,
            last_balance_update_at=last_balance_update_at,
        )
        fields = {k: v for k, v in fields.items() if v is not _UNSET}

        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
        else:
            account = Account(
                institution_connection_id=institution_connection_id,
                plaid_account_id=plaid_account_id,
                **fields,
            )
            db.add(account)

        db.flush()
        return existing if existing else account

    def upsert_many(
        self,
        db: Session,
        institution_connection_id: UUID,
        account_rows: list[dict[str, Any]],
    ) -> list[Account]:
        if not account_rows:
            return []

        plaid_account_ids = [row["plaid_account_id"] for row in account_rows]
        existing_accounts = (
            db.query(Account)
            .filter(
                Account.institution_connection_id == institution_connection_id,
                Account.plaid_account_id.in_(plaid_account_ids),
            )
            .all()
        )
        existing_by_plaid_id = {
            account.plaid_account_id: account for account in existing_accounts
        }

        upserted_accounts: list[Account] = []
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

            account = Account(
                institution_connection_id=institution_connection_id,
                plaid_account_id=plaid_account_id,
                **fields,
            )
            db.add(account)
            upserted_accounts.append(account)

        db.flush()
        return upserted_accounts

    def list_household_accounts(self, db: Session, household_id: UUID):
        return (
            db.query(Account)
            .join(Account.institution_connection)
            .filter(InstitutionConnection.household_id == household_id)
            .order_by(InstitutionConnection.created_at, Account.created_at)
            .all()
        )

    def get_household_account(
        self,
        db: Session,
        *,
        household_id: UUID,
        account_id: UUID,
    ) -> Account | None:
        return (
            db.query(Account)
            .join(Account.institution_connection)
            .filter(
                Account.id == account_id,
                InstitutionConnection.household_id == household_id,
            )
            .first()
        )

    def set_query_tracking_enabled(
        self,
        db: Session,
        *,
        account: Account,
        is_query_tracking_enabled: bool,
    ) -> Account:
        account.is_query_tracking_enabled = is_query_tracking_enabled
        db.flush()
        return account

    def mark_inactive_by_plaid_id(
        self,
        db: Session,
        institution_connection_id: UUID,
        plaid_account_id: str,
    ):
        account = self.get_by_id(
            db=db,
            institution_connection_id=institution_connection_id,
            plaid_account_id=plaid_account_id,
        )
        if account is None:
            return None

        account.is_active = False
        db.flush()
        return account
