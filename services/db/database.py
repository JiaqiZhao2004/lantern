# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:password@localhost:5432/postgres"
)

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True prints SQL to console

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for FastAPI – gives each request its own DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
