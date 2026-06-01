from sqlalchemy.orm import Session
from .repository import HouseholdRepository
from ..household_membership.repository import MembershipRepository
from .models import Household
from ...exceptions import ConflictError, NotFoundError, ValidationError
from uuid import UUID


class HouseholdService:
    def __init__(
        self, household_repo: HouseholdRepository, membership_repo: MembershipRepository
    ):
        self.household_repo = household_repo
        self.membership_repo = membership_repo

    def create_household(
        self, db: Session, user_id: UUID, household_name: str
    ) -> Household:
        normalized_name = household_name.strip()
        if not normalized_name:
            raise ValidationError(detail="Household name cannot be empty")
        existing_membership = self.membership_repo.get_membership_for_user(
            db=db,
            user_id=user_id,
        )
        if existing_membership is not None:
            raise ConflictError(detail="User already belongs to a household")

        household = self.household_repo.create(db=db, name=normalized_name)
        self.membership_repo.create(
            db=db, user_id=user_id, household_id=household.id, role="admin"
        )
        return household

    def get_my_household(self, db: Session, user_id: UUID) -> Household:
        membership = self.membership_repo.get_membership_for_user(
            db=db,
            user_id=user_id,
        )
        if membership is None:
            raise NotFoundError(detail="Membership not found")

        household = self.household_repo.get_by_id(
            db=db,
            household_id=membership.household_id,
        )
        if household is None:
            raise NotFoundError(detail="Household not found")

        return household
