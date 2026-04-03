from fastapi import Depends

from src.app.user.repository import UserRepository
from src.app.user.service import UserService


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(
        user_repo=user_repo,
    )
