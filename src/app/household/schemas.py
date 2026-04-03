# src/app/households/schemas.py

from uuid import UUID
from pydantic import BaseModel


class CreateHouseholdRequest(BaseModel):
    name: str


class HouseholdResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True
