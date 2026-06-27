from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AccountSimpleDTO(BaseModel):
    """A single Account with only the fields the client needs to display it."""

    id: UUID = Field(..., description="Internal app UUID for this account.")
    mask: str | None = Field(None, description="Last 2-4 digits of the account number.")
    name: str = Field(..., description="Account name assigned by the user or institution.")
    official_name: str | None = Field(None, description="Official account name given by the institution.")
    account_type: str | None = Field(None, description="Top-level type: depository, credit, loan, investment, other.")
    account_subtype: str | None = Field(None, description="Subtype: checking, savings, credit card, etc.")
    is_active: bool = Field(..., description="Whether the account is active.")
    is_hidden: bool = Field(..., description="Whether the account has been hidden by the user.")
    is_query_tracking_enabled: bool = Field(
        ...,
        description="Whether the account is tracked by Named Queries.",
    )
    display_order: int | None = Field(None, description="User-defined display ordering.")

    model_config = {"from_attributes": True}


class ConnectionWithAccountsDTO(BaseModel):
    """An InstitutionConnection together with all its Accounts."""

    connection_id: UUID = Field(..., description="Internal app UUID for this connection.")
    institution_name: str | None = Field(None, description="Human-readable institution name, e.g. 'Chase'.")
    status: str = Field(..., description="Connection status: active | revoked | member_departed.")
    accounts: list[AccountSimpleDTO] = Field(
        default_factory=list,
        description="Accounts belonging to this connection, ordered by display_order then name.",
    )


class GetAccountsResponseDTO(BaseModel):
    """All InstitutionConnections with their Accounts for the authenticated user."""

    items: list[ConnectionWithAccountsDTO]


class UpdateAccountTrackingRequestDTO(BaseModel):
    is_query_tracking_enabled: bool = Field(
        ...,
        description="Whether Named Queries should include this account's transactions.",
    )
