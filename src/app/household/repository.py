from sqlalchemy.orm import Session
from uuid import UUID
from .models import Household


class HouseholdRepository:

    def create(self, db: Session, name: str):
        household = Household(name=name)
        db.add(household)
        db.flush()  # ensures household.id is available before commit
        return household

    def get_by_id(self, db: Session, household_id: UUID):
        return db.query(Household).filter(Household.id == household_id).first()
