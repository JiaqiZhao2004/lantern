from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.app import *
from src.infrastructure import get_db, get_firebase_identity
from dataclasses import dataclass


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(
        user_repo=user_repo,
    )


def get_household_repository() -> HouseholdRepository:
    return HouseholdRepository()


def get_membership_repository() -> MembershipRepository:
    return MembershipRepository()


def get_membership_service(
    membership_repo: MembershipRepository = Depends(get_membership_repository),
) -> MembershipService:
    return MembershipService(membership_repo=membership_repo)


def get_household_service(
    household_repo: HouseholdRepository = Depends(get_household_repository),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
) -> HouseholdService:
    return HouseholdService(
        household_repo=household_repo, membership_repo=membership_repo
    )


# Requires User already registered
@dataclass
class RequestContext:
    db: Session
    user: User


# Requires User already registered
def get_current_user(
    db: Session = Depends(get_db),
    firebase_identity: dict = Depends(get_firebase_identity),
    user_repo: UserRepository = Depends(get_user_repository),
):
    firebase_uid = firebase_identity.get("uid")

    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_repo.get_user_by_firebase_uid(db, firebase_uid)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# Requires User already registered
def get_request_context(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RequestContext:

    return RequestContext(
        db=db,
        user=user,
    )
