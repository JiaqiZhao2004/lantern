# src/app/memberships/schemas.py

from uuid import UUID
from pydantic import BaseModel


class MembershipResponse(BaseModel):
    user_id: UUID
    household_id: UUID
    role: str

    class Config:
        from_attributes = True
