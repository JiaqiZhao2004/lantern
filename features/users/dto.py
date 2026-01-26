# features/users/dto.py
# Data Transfer Objects (DTOs) for API requests and responses

from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserResponseDTO(BaseModel):
    id: UUID
    email: EmailStr
    firebase_uid: str
    name: str | None = None

    class Config:
        from_attributes = True
