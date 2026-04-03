from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.app.user import dto
from src.infrastructure import get_db, get_firebase_claims
from ..dependencies import get_user_service
from src.app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/me", response_model=dto.UserResponseDTO)
def get_or_create_me(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_firebase_claims),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.get_or_create_me(db=db, claims=claims)
    except Exception as e:
        return HTTPException(500, e)
