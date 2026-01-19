from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import entities
from db.database import get_db


router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(entities.User).all()
    return users


@router.post("/users")
def create_user(email: str, firebase_uid: str, db: Session = Depends(get_db)):
    user = entities.User(email=email, firebase_uid=firebase_uid)
    db.add(user)
    db.commit()
    db.refresh(user)  # reload with DB-generated fields (id, etc.)
    return user
