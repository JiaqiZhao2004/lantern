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
    expiration: datetime = Field(
        ..., description="Expiry timestamp for the link token."
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


class PlaidItemSimpleDTO(BaseModel):
    """
    A single linked Plaid item (institution connection) belonging to the user.
    """

    id: UUID = Field(..., description="Internal app UUID for this account.")
    institution_name: str | None = Field(
        None,
        description="Human-readable institution name (e.g. 'Chase'), resolved at link time.",
    )
    status: str = Field(..., description="Item status: active | revoked | error.")
    created_at: datetime = Field(..., description="When this item was first linked.")
    updated_at: datetime = Field(..., description="When this item was last modified.")

    model_config = {"from_attributes": True}


class GetItemsResponseDTO(BaseModel):
    """Wrapper around the list of linked Plaid items."""

    items: list[PlaidItemSimpleDTO]
