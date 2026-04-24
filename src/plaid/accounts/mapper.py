from datetime import datetime, timezone
from typing import Any


def plaid_account_to_row(account: dict[str, Any]) -> dict[str, Any]:
    row = {"plaid_account_id": account["account_id"]}

    for field in ("mask", "name", "official_name"):
        if field in account:
            row[field] = account[field]

    if "type" in account:
        row["account_type"] = (
            str(account["type"]) if account["type"] is not None else None
        )
    if "subtype" in account:
        row["account_subtype"] = (
            str(account["subtype"]) if account["subtype"] is not None else None
        )

    if "balances" in account:
        balances = account.get("balances") or {}
        for plaid_key, model_key in {
            "current": "current_balance",
            "available": "available_balance",
            "limit": "limit_amount",
            "iso_currency_code": "iso_currency_code",
            "unofficial_currency_code": "unofficial_currency_code",
        }.items():
            if plaid_key in balances:
                row[model_key] = balances[plaid_key]

        if "last_updated_datetime" in balances:
            last_updated = balances["last_updated_datetime"]
            if last_updated is None:
                row["last_balance_update_at"] = None
            else:
                last_balance_update_at = (
                    last_updated
                    if isinstance(last_updated, datetime)
                    else datetime.fromisoformat(str(last_updated))
                )
                if last_balance_update_at.tzinfo is None:
                    last_balance_update_at = last_balance_update_at.replace(
                        tzinfo=timezone.utc
                    )
                else:
                    last_balance_update_at = last_balance_update_at.astimezone(
                        timezone.utc
                    )
                row["last_balance_update_at"] = last_balance_update_at

    return row


def plaid_accounts_to_rows(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [plaid_account_to_row(account) for account in accounts]
