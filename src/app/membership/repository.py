# src/app/memberships/repository.py

from sqlalchemy.orm import Session
from .models import HouseholdMembership
from uuid import UUID


class MembershipRepository:
    def create(
        self,
        db: Session,
        user_id: UUID,
        household_id: UUID,
        role: str,
    ) -> HouseholdMembership:
        membership = HouseholdMembership(
            user_id=user_id,
            household_id=household_id,
            role=role,
        )
        db.add(membership)
        db.flush()
        return membership

    def get_membership(self, db: Session, user_id: UUID, household_id: UUID):
        return (
            db.query(HouseholdMembership)
            .filter(
                HouseholdMembership.user_id == user_id,
                HouseholdMembership.household_id == household_id,
            )
            .first()
        )

    def get_membership_for_user(self, db: Session, user_id: UUID):
        return (
            db.query(HouseholdMembership)
            .filter(HouseholdMembership.user_id == user_id)
            .first()
        )

    def delete_membership(
        self, db: Session, user_id: UUID, household_id: UUID
    ) -> HouseholdMembership | None:
        membership = self.get_membership(
            db=db, user_id=user_id, household_id=household_id
        )
        if membership is None:
            return None

        db.delete(membership)
        db.flush()
        return membership

    def list_members_for_household(self, db: Session, household_id: UUID):
        return (
            db.query(HouseholdMembership)
            .filter(HouseholdMembership.household_id == household_id)
            .all()
        )
