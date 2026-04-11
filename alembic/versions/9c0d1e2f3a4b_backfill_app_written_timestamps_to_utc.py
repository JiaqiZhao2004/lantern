"""backfill app-written timestamps to utc

Revision ID: 9c0d1e2f3a4b
Revises: 7e137f286006
Create Date: 2026-04-11 02:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c0d1e2f3a4b"
down_revision: Union[str, Sequence[str], None] = "7e137f286006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UPGRADE_TEMPLATE = """
UPDATE {table}
SET {column} = ({column} AT TIME ZONE 'UTC') AT TIME ZONE 'America/Chicago'
WHERE {column} IS NOT NULL
"""

DOWNGRADE_TEMPLATE = """
UPDATE {table}
SET {column} = ({column} AT TIME ZONE 'America/Chicago') AT TIME ZONE 'UTC'
WHERE {column} IS NOT NULL
"""

TARGET_COLUMNS: tuple[tuple[str, str], ...] = (
    ("plaid_accounts", "last_balance_update_at"),
    ("plaid_items", "last_synced_at"),
    # sync_jobs currently has 0 rows in the live DB, but keep it covered.
    ("sync_jobs", "next_attempt_at"),
    ("sync_jobs", "started_at"),
    ("sync_jobs", "finished_at"),
)


def _rewrite_columns(template: str) -> None:
    for table, column in TARGET_COLUMNS:
        op.execute(sa.text(template.format(table=table, column=column)))


def upgrade() -> None:
    """Upgrade schema."""
    _rewrite_columns(UPGRADE_TEMPLATE)


def downgrade() -> None:
    """Downgrade schema."""
    _rewrite_columns(DOWNGRADE_TEMPLATE)
