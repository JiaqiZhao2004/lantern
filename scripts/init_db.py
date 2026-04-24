# scripts/init_db.py
from src.infrastructure.db.database import Base, engine

# Import entities so they register with SQLAlchemy metadata.
import src.app.household.models
import src.app.membership.models
import src.app.user.models
import src.plaid.accounts.models
import src.plaid.items.models
import src.sync.jobs.models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
