from fastapi import APIRouter, Depends, HTTPException
from psycopg import IntegrityError
from sqlalchemy.orm import Session

from src.app.user import dto
from src.app.user import entities
from src.infrastructure import get_db, get_firebase_claims


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/me", response_model=dto.UserResponseDTO)
def get_or_create_me(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_firebase_claims),
):
    firebase_uid = claims["uid"]
    email = claims["email"]

    # Try to find existing user by firebase_uid
    db_user = (
        db.query(entities.User)
        .filter(entities.User.firebase_uid == firebase_uid)
        .first()
    )
    if db_user:
        return db_user

    # Create user row owned by this token identity
    db_user = entities.User(firebase_uid=firebase_uid, email=email)
    db.add(db_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Handles race condition: two requests create at once
        db_user = (
            db.query(entities.User)
            .filter(entities.User.firebase_uid == firebase_uid)
            .first()
        )
        if db_user:
            return db_user
        raise HTTPException(status_code=500, detail="Failed to create user")

    db.refresh(db_user)
    return db_user
