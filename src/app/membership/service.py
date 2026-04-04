from sqlalchemy.orm import Session
from .repository import MembershipRepository
from .models import HouseholdMembership
from ..household.repository import HouseholdRepository
from ..exceptions import ConflictError, NotFoundError
from uuid import UUID


class MembershipService:
    def __init__(
        self,
        membership_repo: MembershipRepository,
        household_repo: HouseholdRepository,
    ):
        self.membership_repo = membership_repo
        self.household_repo = household_repo

    def join_household(
        self, db: Session, user_id: UUID, household_id: UUID
    ) -> HouseholdMembership:
        household = self.household_repo.get_by_id(db=db, household_id=household_id)
        if household is None:
            raise NotFoundError(detail="Household not found")

        existing_membership = self.membership_repo.get_membership(
            db=db,
            user_id=user_id,
            household_id=household_id,
        )
        if existing_membership is not None:
            raise ConflictError(detail="Membership already exists")

        try:
            household_membership = self.membership_repo.create(
                db=db, user_id=user_id, household_id=household_id, role="member"
            )
            db.commit()
            db.refresh(household_membership)
            return household_membership
        except Exception:
            db.rollback()
            raise

    def leave_household(self, db: Session, user_id: UUID, household_id: UUID) -> None:
        household = self.household_repo.get_by_id(db=db, household_id=household_id)
        if household is None:
            raise NotFoundError(detail="Household not found")

        try:
            membership = self.membership_repo.delete_membership(
                db=db, user_id=user_id, household_id=household_id
            )
            if membership is None:
                db.rollback()
                raise NotFoundError(detail="Membership not found")

            db.commit()
        except NotFoundError:
            raise
        except Exception:
            db.rollback()
            raise
