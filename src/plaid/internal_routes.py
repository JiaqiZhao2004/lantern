# features/plaid/internal_routes.py
# Internal-only endpoints — never exposed to clients.
# Protected by X-Internal-Secret header; hidden from public OpenAPI docs.

import json
import os
from datetime import datetime

import plaid
from fastapi import APIRouter, Depends, Header, HTTPException
from plaid.model.accounts_get_request import AccountsGetRequest
from sqlalchemy.orm import Session

from src.plaid.entities import PlaidAccount, PlaidItem
from src.plaid.plaid_client import client
from services import get_db
from services.aws.kms import decrypt_secret

# ---------- Internal auth ----------


def _require_internal_secret(
    x_internal_secret: str = Header(
        ...,
        description="Shared secret for server-to-server calls. Set INTERNAL_SECRET in env.",
    ),
) -> None:
    """Dependency that blocks any request whose X-Internal-Secret header does not
    match the INTERNAL_SECRET environment variable.  Never expose to clients."""
    expected = os.getenv("INTERNAL_SECRET", "")
    if not expected or x_internal_secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


# ---------- Helpers ----------


def _sync_accounts_for_item(item: PlaidItem, db: Session) -> int:
    """
    Pull the latest account list from Plaid for *item* and upsert every
    account into the plaid_accounts table.

    Returns the number of accounts upserted.

    This is intentionally a plain function (not a route) so it can be called:
      - directly from add_item after the item is persisted, and
      - from the internal /internal/sync_accounts/{plaid_item_id} endpoint
        triggered by webhooks or schedulers.
    """
    # 1. Recover the plaintext access token via KMS envelope decryption
    access_token = decrypt_secret(
        item.access_token_encrypted_data_key,
        item.access_token_nonce,
        item.access_token_ciphertext,
    )

    # 2. Call Plaid /accounts/get
    resp = client.accounts_get(AccountsGetRequest(access_token=access_token))
    accounts = resp["accounts"]

    # 3. Upsert each account
    for acc in accounts:
        balances = acc.get("balances", {})
        plaid_account_id: str = acc["account_id"]

        existing = (
            db.query(PlaidAccount)
            .filter_by(item_id=item.id, plaid_account_id=plaid_account_id)
            .first()
        )

        last_balance_update_raw = balances.get("last_updated_datetime")
        last_balance_update_at: datetime | None = None
        if last_balance_update_raw is not None:
            if isinstance(last_balance_update_raw, datetime):
                last_balance_update_at = last_balance_update_raw
            else:
                last_balance_update_at = datetime.fromisoformat(
                    str(last_balance_update_raw)
                )

        fields = dict(
            mask=acc.get("mask"),
            name=acc.get("name"),
            official_name=acc.get("official_name"),
            account_type=str(acc["type"]) if acc.get("type") is not None else None,
            account_subtype=(
                str(acc["subtype"]) if acc.get("subtype") is not None else None
            ),
            current_balance=balances.get("current"),
            available_balance=balances.get("available"),
            limit_amount=balances.get("limit"),
            iso_currency_code=balances.get("iso_currency_code"),
            unofficial_currency_code=balances.get("unofficial_currency_code"),
            last_balance_update_at=last_balance_update_at,
        )

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
        else:
            db.add(
                PlaidAccount(
                    item_id=item.id,
                    plaid_account_id=plaid_account_id,
                    **fields,
                )
            )

    db.commit()
    return len(accounts)


# ---------- Router ----------

internal_router = APIRouter(prefix="/internal", tags=["internal"])


@internal_router.post(
    "/sync_accounts/{plaid_item_id}",
    summary="Re-sync accounts for a Plaid item (internal use only)",
    include_in_schema=False,  # hide from public OpenAPI docs
)
def sync_accounts(
    plaid_item_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(_require_internal_secret),
):
    """
    Pull the latest account list from Plaid and upsert into plaid_accounts.

    Intended callers:
      - Plaid NEW_ACCOUNTS_AVAILABLE webhook handler
      - Scheduled background job
      - Admin tooling

    Protected by X-Internal-Secret header — never call from the client.
    """
    item = db.query(PlaidItem).filter(PlaidItem.plaid_item_id == plaid_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.status != "active":
        raise HTTPException(
            status_code=409, detail=f"Item status is '{item.status}', skipping sync"
        )

    try:
        count = _sync_accounts_for_item(item, db)
    except plaid.ApiException as e:
        raise HTTPException(status_code=502, detail=json.loads(e.body))  # type: ignore

    return {"synced_accounts": count}
