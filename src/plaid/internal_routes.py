# # features/plaid/internal_routes.py
# # Internal-only endpoints — never exposed to clients.
# # Protected by X-Internal-Secret header; hidden from public OpenAPI docs.

# import json
# import os
# from datetime import datetime

# import plaid
# from fastapi import APIRouter, Depends, Header, HTTPException
# from plaid.model.accounts_get_request import AccountsGetRequest
# from sqlalchemy.orm import Session

# from src.infrastructure import get_db, get_kms_service
# from src.infrastructure.aws.kms import KMSService
# from src.plaid.items.models import PlaidAccount, PlaidItem
# from src.infrastructure.plaid.client import client

# # ---------- Internal auth ----------


# def _require_internal_secret(
#     x_internal_secret: str = Header(
#         ...,
#         description="Shared secret for server-to-server calls. Set INTERNAL_SECRET in env.",
#     ),
# ) -> None:
#     """Dependency that blocks any request whose X-Internal-Secret header does not
#     match the INTERNAL_SECRET environment variable.  Never expose to clients."""
#     expected = os.getenv("INTERNAL_SECRET", "")
#     if not expected or x_internal_secret != expected:
#         raise HTTPException(status_code=403, detail="Forbidden")


# # ---------- Helpers ----------




# # ---------- Router ----------

# internal_router = APIRouter(prefix="/internal", tags=["internal"])


# @internal_router.post(
#     "/sync_accounts/{plaid_item_id}",
#     summary="Re-sync accounts for a Plaid item (internal use only)",
#     include_in_schema=False,  # hide from public OpenAPI docs
# )
# def sync_accounts(
#     plaid_item_id: str,
#     db: Session = Depends(get_db),
#     kms: KMSService = Depends(get_kms_service),
#     _: None = Depends(_require_internal_secret),
# ):
#     """
#     Pull the latest account list from Plaid and upsert into plaid_accounts.

#     Intended callers:
#       - Plaid NEW_ACCOUNTS_AVAILABLE webhook handler
#       - Scheduled background job
#       - Admin tooling

#     Protected by X-Internal-Secret header — never call from the client.
#     """
#     item = db.query(PlaidItem).filter(PlaidItem.plaid_item_id == plaid_item_id).first()
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     if item.status != "active":
#         raise HTTPException(
#             status_code=409, detail=f"Item status is '{item.status}', skipping sync"
#         )

#     try:
#         count = _sync_accounts_for_item(item, db, kms)
#     except plaid.ApiException as e:
#         raise HTTPException(status_code=502, detail=json.loads(e.body))  # type: ignore

#     return {"synced_accounts": count}
