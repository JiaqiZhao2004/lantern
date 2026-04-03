from fastapi import Depends
from sqlalchemy.orm import Session

from src.app.user.repository import UserRepository
from src.app.user.service import UserService

from src.infrastructure import get_db, get_firebase_claims
from dataclasses import dataclass


@dataclass
class RequestContext:
    db: Session
    claims: dict


def get_request_context(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_firebase_claims),
) -> RequestContext:
    return RequestContext(
        db=db,
        claims=claims,
    )


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(
        user_repo=user_repo,
    )
