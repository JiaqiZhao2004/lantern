# scripts/init_db.py
from services.db.database import engine, Base
# ImportError: attempted relative import with no known parent package
# IMPORTANT: import entities so they register
import features.users.entities
import features.plaid.entities

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
