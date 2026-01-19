# scripts/init_db.py
from services.db.database import engine, Base

# IMPORTANT: import entities so they register
import features.users.entities

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
