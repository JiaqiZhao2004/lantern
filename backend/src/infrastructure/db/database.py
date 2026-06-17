# database.py
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True prints SQL to console


@event.listens_for(engine, "connect")
def set_postgres_utc_timezone(dbapi_connection, _):
    with dbapi_connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for FastAPI – gives each request its own DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
