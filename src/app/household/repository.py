from sqlalchemy.orm import Session

from .models import Household


class HouseholdRepository:

    def create(self, db: Session, name: str):
        household = Household(name=name)
        db.add(household)
        db.flush()  # ensures household.id is available before commit
        return household

    def get_by_id(self, db: Session, household_id: str):
        return db.query(Household).filter(Household.id == household_id).first()
