# features/plaid/dto.py
# Pydantic DTOs for Plaid API request/response shapes.
# These are the types exposed in the OpenAPI schema consumed by the frontend.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# GET /accounts
# ---------------------------------------------------------------------------


class AccountSimpleDTO(BaseModel):
    """
    A single bank account within a linked item, with only the fields the
    client needs to display it.  Sensitive / internal fields are omitted.
    """
    id: UUID = Field(..., description="Internal app UUID for this account.")
    mask: str | None = Field(None, description="Last 2-4 digits of the account number.")
    name: str = Field(
        ..., description="Account name assigned by the user or institution."
    )
    official_name: str | None = Field(
        None, description="Official account name given by the institution."
    )
    account_type: str | None = Field(
        None, description="Top-level type: depository, credit, loan, investment, other."
    )
    account_subtype: str | None = Field(
        None, description="Subtype: checking, savings, credit card, etc."
    )
    is_active: bool = Field(..., description="Whether the account is active.")
    is_hidden: bool = Field(
        ..., description="Whether the account has been hidden by the user."
    )
    display_order: int | None = Field(
        None, description="User-defined display ordering."
    )

    model_config = {"from_attributes": True}


class ItemWithAccountsDTO(BaseModel):
    """
    A linked item (institution connection) together with all its accounts.
    This is the primary shape the client uses to render the accounts list.
    """

    item_id: UUID = Field(..., description="Internal app UUID for this item.")
    institution_name: str | None = Field(
        None, description="Human-readable institution name, e.g. 'Chase'."
    )
    status: str = Field(..., description="Item status: active | revoked | error.")
    accounts: list[AccountSimpleDTO] = Field(
        default_factory=list,
        description="Accounts belonging to this item, ordered by display_order then name.",
    )


class GetAccountsResponseDTO(BaseModel):
    """All items with their accounts for the authenticated user."""

    items: list[ItemWithAccountsDTO]
