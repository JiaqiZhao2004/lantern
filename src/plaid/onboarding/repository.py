from sqlalchemy.orm import Session
from uuid import UUID
from .models import PlaidItem, PlaidAccount
from ...app.user.models import User


class PlaidItemRepository:

    def create(
        self,
        db: Session,
        user: User,
        plaid_item_id: str,
        institution_id: str,
        institution_name: str,
    ):
        household = PlaidItem()
        db.add(household)
        db.flush()  # ensures household.id is available before commit
        return household

    def get_by_id(self, db: Session, household_id: UUID):
        return db.query(PlaidItem).filter(PlaidItem.id == household_id).first()
