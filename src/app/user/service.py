from sqlalchemy.orm import Session
from .repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_or_create_me(
        self,
        db: Session,
        firebase_identity: dict,
    ):
        firebase_uid = firebase_identity["uid"]
        email = firebase_identity["email"]

        # Try to find existing user by firebase_uid
        db_user = self.user_repo.get_user_by_firebase_uid(db, firebase_uid)
        if db_user:
            return db_user

        # Create user row owned by this token identity
        self.user_repo.create_user(db, firebase_uid, email)
        return db_user
