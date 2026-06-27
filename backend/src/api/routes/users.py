from fastapi import APIRouter, Depends

from src.modules.user import schemas
from src.infrastructure.auth_access import ensure_identity_authorized
from ..dependencies import (
    get_user_service,
    get_firebase_identity,
    get_db,
)
from src.modules.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/me", response_model=schemas.UserResponseDTO)
def get_or_create_me(
    db=Depends(get_db),
    firebase_identity: dict = Depends(get_firebase_identity),
    user_service: UserService = Depends(get_user_service),
):
    ensure_identity_authorized(firebase_identity)

    try:
        user = user_service.get_or_create_me(db=db, firebase_identity=firebase_identity)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user
