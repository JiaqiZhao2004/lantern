from fastapi import APIRouter, Depends, HTTPException

from src.app.user import schemas
from ..dependencies import (
    get_user_service,
    get_firebase_identity,
    get_db,
)
from src.app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/me", response_model=schemas.UserResponseDTO)
def get_or_create_me(
    db=Depends(get_db),
    firebase_identity: dict = Depends(get_firebase_identity),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.get_or_create_me(db=db, firebase_identity=firebase_identity)
    except Exception as e:
        return HTTPException(500, e)
