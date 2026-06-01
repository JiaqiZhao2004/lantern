from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import User


class UserRepository:

    def get_user_by_firebase_uid(self, db: Session, firebase_uid: str) -> User | None:
        return db.query(User).filter(User.firebase_uid == firebase_uid).first()

    def create_user(self, db: Session, firebase_uid: str, email: str):
        db_user = User(firebase_uid=firebase_uid, email=email)
        db.add(db_user)
        db.flush()
        return db_user
