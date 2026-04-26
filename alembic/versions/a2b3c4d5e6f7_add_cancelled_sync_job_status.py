"""add cancelled sync job status

Revision ID: a2b3c4d5e6f7
Revises: 9c0d1e2f3a4b
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "9c0d1e2f3a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("ALTER TYPE sync_status ADD VALUE IF NOT EXISTS 'cancelled'"))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            """
            UPDATE sync_jobs
            SET status = 'dead_letter'
            WHERE status = 'cancelled'
            """
        )
    )
    op.execute(sa.text("ALTER TYPE sync_status RENAME TO sync_status_old"))
    op.execute(
        sa.text(
            """
            CREATE TYPE sync_status AS ENUM (
                'queued',
                'running',
                'succeeded',
                'dead_letter'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE sync_jobs
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE sync_status
            USING status::text::sync_status,
            ALTER COLUMN status SET DEFAULT 'queued'
            """
        )
    )
    op.execute(sa.text("DROP TYPE sync_status_old"))
