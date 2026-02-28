import os
import json
import time
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import plaid
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_statements import (
    LinkTokenCreateRequestStatements,
)
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.api import plaid_api

from services import get_db, get_firebase_claims
from services.aws import encrypt_secret
from features.plaid.dto import (
    AddItemResponseDTO,
    CreateLinkTokenResponseDTO,
    GetItemsResponseDTO,
    PlaidItemDTO,
)
from features.plaid.entities import PlaidItem
from features.users.entities import User

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")
SIGNAL_RULESET_KEY = os.getenv("SIGNAL_RULESET_KEY", "")


def empty_to_none(field: str) -> Optional[str]:
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value


host = plaid.Environment.Sandbox
if PLAID_ENV == "sandbox":
    host = plaid.Environment.Sandbox
if PLAID_ENV == "production":
    host = plaid.Environment.Production

PLAID_REDIRECT_URI = empty_to_none("PLAID_REDIRECT_URI")

configuration = plaid.Configuration(
    host=host,
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "plaidVersion": "2020-09-14",
    },
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

products = [Products(p) for p in PLAID_PRODUCTS]

# ---------- Routes ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])


@router.post("/create_link_token", response_model=CreateLinkTokenResponseDTO)
def create_link_token():
    try:
        req = LinkTokenCreateRequest(
            products=products,
            client_name="Plaid Quickstart",
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(time.time())),
        )

        if PLAID_REDIRECT_URI is not None:
            req["redirect_uri"] = PLAID_REDIRECT_URI  # type: ignore

        if Products("statements") in products:
            req["statements"] = LinkTokenCreateRequestStatements(  # type: ignore
                end_date=date.today(),
                start_date=date.today() - timedelta(days=30),
            )

        resp = client.link_token_create(req)
        return resp.to_dict()
    except plaid.ApiException as e:
        return JSONResponse(status_code=e.status, content=json.loads(e.body))  # type: ignore


@router.post("/item", response_model=AddItemResponseDTO)
def add_item(
    public_token: str = Form(...),
    db: Session = Depends(get_db),
    claims: dict = Depends(get_firebase_claims),
):
    """
    Exchange a Plaid public_token for a persistent access_token.
    The access_token is envelope-encrypted with KMS (AES-256-GCM) and
    stored in the plaid_items table alongside the KMS-encrypted data key.
    """
    # 1. Exchange public token with Plaid
    try:
        req = ItemPublicTokenExchangeRequest(public_token=public_token)
        resp = client.item_public_token_exchange(req)
    except plaid.ApiException as e:
        return JSONResponse(status_code=e.status, content=json.loads(e.body))  # type: ignore

    plaid_access_token: str = resp["access_token"]
    plaid_item_id: str = resp["item_id"]

    # 2. Look up the calling user
    firebase_uid: str = claims["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Envelope-encrypt the access_token with KMS
    ciphertext, nonce, encrypted_data_key = encrypt_secret(plaid_access_token)

    # 4. Get institution_id and institution_name
    institution_id = None
    institution_name = None
    try:
        item_resp = client.item_get(ItemGetRequest(access_token=plaid_access_token))
        institution_id = item_resp.get("item", {}).get("institution_id")
        if institution_id:
            inst_resp = client.institutions_get_by_id(
                InstitutionsGetByIdRequest(
                    institution_id=institution_id,
                    country_codes=list(
                        map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)
                    ),
                )
            )
            institution_name = inst_resp.get("institution", {}).get("name")
    except Exception:
        pass  # Institution info is optional

    # 5. Persist the PlaidItem
    db_item = PlaidItem(
        user_id=user.id,
        plaid_item_id=plaid_item_id,
        institution_id=institution_id,
        institution_name=institution_name,
        access_token_ciphertext=ciphertext,
        access_token_nonce=nonce,
        access_token_encrypted_data_key=encrypted_data_key,
        kms_key_id=os.getenv("KMS_KEY_ID"),  # Store which KMS key was used
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return {"item_id": plaid_item_id, "status": "ok"}


@router.get("/items", response_model=GetItemsResponseDTO)
def get_items(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_firebase_claims),
):
    """
    Return all Plaid items belonging to the authenticated user.

    NOTE: Access tokens are returned as raw encrypted bytes — they are NOT
    decrypted here.  Callers should treat these fields as opaque.

    TODO: Replace raw row serialisation with a proper response DTO/schema
          (e.g. a Pydantic model) that explicitly controls which fields are
          exposed.  At minimum, omit the ciphertext fields from the public
          response once decryption is wired up.
    TODO: Decrypt access_token_ciphertext via KMS before using the token for
          any downstream Plaid API calls (see services/aws/kms.py).
    TODO: Add pagination (skip / limit) if a user can have many linked items.
    """
    # 1. Resolve the calling user
    firebase_uid: str = claims["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Fetch all PlaidItems for this user
    items = db.query(PlaidItem).filter(PlaidItem.user_id == user.id).all()

    # 3. Serialise via DTO
    return GetItemsResponseDTO(
        items=[
            PlaidItemDTO(
                id=item.id,
                plaid_item_id=item.plaid_item_id,
                institution_id=item.institution_id,
                institution_name=item.institution_name,
                status=item.status,
                kms_key_id=item.kms_key_id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                # TODO: remove these three fields once decryption is wired up
                access_token_ciphertext=item.access_token_ciphertext.hex(),
                access_token_nonce=item.access_token_nonce.hex(),
                access_token_encrypted_data_key=item.access_token_encrypted_data_key.hex(),
            )
            for item in items
        ]
    )
