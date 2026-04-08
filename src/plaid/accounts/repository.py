from sqlalchemy.orm import Session
from datetime import datetime
from .models import PlaidAccount


class PlaidAccountRepository:

    def get_by_id(
        self,
        db: Session,
        plaid_item_id: str,
        plaid_account_id: str,
    ):
        return (
            db.query(PlaidAccount)
            .filter_by(item_id=plaid_item_id, plaid_account_id=plaid_account_id)
            .first()
        )

    def create_or_update(
        self,
        db: Session,
        plaid_item_id: str,
        plaid_account_id: str,
        mask: str | None = None,
        name: str | None = None,
        official_name: str | None = None,
        account_type: str | None = None,
        account_subtype: str | None = None,
        current_balance: float | None = None,
        available_balance: float | None = None,
        limit_amount: float | None = None,
        iso_currency_code: str | None = None,
        unofficial_currency_code: str | None = None,
        owner_names: dict | None = None,
        is_active: bool | None = None,
        is_hidden: bool | None = None,
        display_order: int | None = None,
        last_balance_update_at: datetime | None = None,
    ) -> PlaidAccount:
        existing = self.get_by_id(
            db=db, plaid_item_id=plaid_item_id, plaid_account_id=plaid_account_id
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

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)

        else:
            account = PlaidAccount(
                item_id=plaid_item_id,
                plaid_account_id=plaid_account_id,
                **fields,
            )
            db.add(account)

        db.flush()
        return existing if existing else account
