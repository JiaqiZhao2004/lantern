from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CreateLinkTokenResponseDTO(BaseModel):
    """Plaid link token returned to the frontend to initialise Plaid Link."""

    link_token: str = Field(
        ..., description="Opaque token passed to Plaid Link on the client."
    )
    expiration: datetime = Field(
        ..., description="Expiry timestamp for the link token."
    )
    request_id: str = Field(..., description="Plaid request ID for debugging.")


class InstitutionConnectionSimpleDTO(BaseModel):
    """A single linked institution connection belonging to the user."""

    id: UUID = Field(..., description="Internal app UUID for this connection.")
    institution_name: str | None = Field(
        None,
        description="Human-readable institution name (e.g. 'Chase'), resolved at link time.",
    )
    status: str = Field(..., description="Connection status: active | revoked | member_departed.")
    can_revoke: bool = Field(
        ...,
        description="Whether the authenticated user may revoke this connection.",
    )
    created_at: datetime = Field(..., description="When this connection was first linked.")
    updated_at: datetime = Field(..., description="When this connection was last modified.")

    model_config = {"from_attributes": True}


class GetConnectionsResponseDTO(BaseModel):
    """Wrapper around the list of linked institution connections."""

    items: list[InstitutionConnectionSimpleDTO]
