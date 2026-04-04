from fastapi import HTTPException
from sqlalchemy.orm import Session
from .repository import MembershipRepository
from .models import HouseholdMembership
from uuid import UUID


class MembershipService:
    def __init__(
        self,
        membership_repo: MembershipRepository,
    ):
        self.membership_repo = membership_repo

    def join_household(
        self, db: Session, user_id: UUID, household_id: UUID
    ) -> HouseholdMembership:
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
        try:
            membership = self.membership_repo.delete_membership(
                db=db, user_id=user_id, household_id=household_id
            )
            if membership is None:
                db.rollback()
                raise HTTPException(status_code=404, detail="Membership not found")

            db.commit()
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            raise
