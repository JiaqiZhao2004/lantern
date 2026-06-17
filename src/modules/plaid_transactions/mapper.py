from typing import Any
from uuid import UUID

from .models import InterbankTransferInfo, PaymentChannel


def interbank_transfer_info(tx: dict[str, Any]) -> InterbankTransferInfo | None:
    payment_meta = tx.get("payment_meta") or {}

    info: InterbankTransferInfo = {
        "reference_number": payment_meta.get("reference_number"),
        "ppd_id": payment_meta.get("ppd_id"),
        "payee": payment_meta.get("payee"),
        "by_order_of": payment_meta.get("by_order_of"),
        "payer": payment_meta.get("payer"),
        "payment_method": payment_meta.get("payment_method"),
        "payment_processor": payment_meta.get("payment_processor"),
        "reason": payment_meta.get("reason"),
    }

    if all(value is None or value == "" for value in info.values()):
        return None

    return info


def plaid_transaction_to_row(
    tx: dict[str, Any],
    *,
    account_id: UUID,
    item_id: UUID,
    household_id: UUID,
) -> dict[str, Any]:
    personal_finance_category = tx.get("personal_finance_category")

    return {
        "plaid_transaction_id": tx["transaction_id"],
        "account_id": account_id,
        "item_id": item_id,
        "household_id": household_id,
        "is_removed": False,
        "pending": tx["pending"],
        "amount": -tx["amount"],
        "authorized_date": tx["authorized_date"],
        "posted_date": tx["date"],
        "occurred_at": tx["authorized_date"] if tx["authorized_date"] else tx["date"],
        "merchant_name": tx["merchant_name"],
        "category_primary": (
            personal_finance_category["primary"] if personal_finance_category else None
        ),
        "category_detailed": (
            personal_finance_category["detailed"] if personal_finance_category else None
        ),
        "iso_currency_code": tx["iso_currency_code"],
        "pending_transaction_id": tx["pending_transaction_id"],
        "payment_channel": PaymentChannel(tx["payment_channel"]),
        "check_number": tx["check_number"],
        "original_description": tx.get("original_description"),
        "interbank_transfer_info": interbank_transfer_info(tx),
        "logo_url": tx["logo_url"],
        "removed_at": None,
    }


def plaid_transactions_to_rows(
    transactions: list[dict[str, Any]],
    *,
    account_id: UUID,
    item_id: UUID,
    household_id: UUID,
) -> list[dict[str, Any]]:
    return [
        plaid_transaction_to_row(
            tx,
            account_id=account_id,
            item_id=item_id,
            household_id=household_id,
        )
        for tx in transactions
    ]
