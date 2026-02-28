# features/plaid/dto.py
# Pydantic DTOs for Plaid API request/response shapes.
# These are the types exposed in the OpenAPI schema consumed by the frontend.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /create_link_token
# ---------------------------------------------------------------------------


class CreateLinkTokenResponseDTO(BaseModel):
    """Plaid link token returned to the frontend to initialise Plaid Link."""

    link_token: str = Field(
        ..., description="Opaque token passed to Plaid Link on the client."
    )
    expiration: str = Field(
        ..., description="ISO-8601 expiry timestamp for the link token."
    )
    request_id: str = Field(..., description="Plaid request ID for debugging.")


# ---------------------------------------------------------------------------
# POST /item
# ---------------------------------------------------------------------------


class AddItemResponseDTO(BaseModel):
    """Confirmation returned after a public token is successfully exchanged."""

    item_id: str = Field(
        ..., description="Plaid item_id for the newly linked institution."
    )
    status: str = Field("ok", description="Always 'ok' on success.")


# ---------------------------------------------------------------------------
# GET /items
# ---------------------------------------------------------------------------


class PlaidItemDTO(BaseModel):
    """
    A single linked Plaid item (institution connection) belonging to the user.

    Encrypted credential fields are intentionally omitted from this DTO.
    TODO: Remove access_token_* fields below once decryption + a dedicated
          'fetch transactions' endpoint is implemented — they should never
          be sent over the wire in production.
    """

    id: UUID = Field(..., description="Internal app UUID for this Plaid item.")
    plaid_item_id: str = Field(..., description="Plaid's own item identifier.")
    institution_id: str | None = Field(
        None, description="Plaid institution_id, if available."
    )
    institution_name: str | None = Field(
        None,
        description="Human-readable institution name (e.g. 'Chase'), resolved at link time.",
    )
    status: str = Field(..., description="Item status: active | revoked | error.")
    kms_key_id: str | None = Field(
        None, description="KMS CMK used to encrypt the access token."
    )
    created_at: datetime = Field(..., description="When this item was first linked.")
    updated_at: datetime = Field(..., description="When this item was last modified.")

    # TODO: Remove these three fields once decryption is wired up server-side.
    #       They are raw encrypted bytes (hex-encoded) and must never be
    #       forwarded to Plaid or exposed to end users.
    access_token_ciphertext: str = Field(
        ...,
        description="[TEMP] Hex-encoded AES-GCM ciphertext of the Plaid access token.",
    )
    access_token_nonce: str = Field(
        ...,
        description="[TEMP] Hex-encoded AES-GCM nonce used when encrypting the access token.",
    )
    access_token_encrypted_data_key: str = Field(
        ..., description="[TEMP] Hex-encoded KMS-encrypted data key (CiphertextBlob)."
    )

    model_config = {"from_attributes": True}


class GetItemsResponseDTO(BaseModel):
    """Wrapper around the list of linked Plaid items."""

    items: list[PlaidItemDTO]
