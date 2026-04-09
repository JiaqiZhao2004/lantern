# scripts/init_db.py
from src.infrastructure.db.database import engine, Base

# ImportError: attempted relative import with no known parent package
# IMPORTANT: import entities so they register
import src.app.user.models
import src.app.household.models
import src.app.membership.models
import src.plaid.items.models
import src.plaid.accounts.models
import src.sync.jobs.models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
