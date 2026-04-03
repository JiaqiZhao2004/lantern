from sqlalchemy.orm import Session
from .repository import HouseholdRepository
from ..membership.repository import MembershipRepository
from .models import Household
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
        try:
            # create household and create household membership: creator as admin
            household = self.household_repo.create(db=db, name=household_name)
            self.membership_repo.create(
                db=db, user_id=user_id, household_id=household.id, role="admin"
            )
            db.commit()
            db.refresh(household)
            return household
        except Exception:
            db.rollback()
            raise
