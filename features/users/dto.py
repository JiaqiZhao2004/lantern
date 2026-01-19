# features/users/dto.py
# Data Transfer Objects (DTOs) for API requests and responses

from pydantic import BaseModel, EmailStr


class UserResponseDTO(BaseModel):
    id: int
    email: EmailStr
    firebase_uid: str
    name: str | None = None

    class Config:
        from_attributes = True
