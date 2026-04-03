from fastapi import APIRouter, Depends, HTTPException

from src.app.user import dto
from ..dependencies import (
    get_user_service,
    get_request_context,
    RequestContext,
)
from src.app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/me", response_model=dto.UserResponseDTO)
def get_or_create_me(
    ctx: RequestContext = Depends(get_request_context),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.get_or_create_me(db=ctx.db, claims=ctx.claims)
    except Exception as e:
        return HTTPException(500, e)
