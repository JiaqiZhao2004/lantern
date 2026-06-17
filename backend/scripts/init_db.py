# scripts/init_db.py
from src.infrastructure.db.database import Base, engine

# Import entities so they register with SQLAlchemy metadata.
import src.modules.household.models
import src.modules.household_membership.models
import src.modules.user.models
import src.modules.plaid_accounts.models
import src.modules.plaid_items.models
import src.modules.plaid_transaction_sync_jobs.models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
