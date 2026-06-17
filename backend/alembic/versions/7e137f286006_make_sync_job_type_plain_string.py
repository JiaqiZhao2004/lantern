"""remove scheduled_fallback from job_type enum

Revision ID: 7e137f286006
Revises: d40b1cadd914
Create Date: 2026-04-10 23:20:55.648726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7e137f286006'
down_revision: Union[str, Sequence[str], None] = 'd40b1cadd914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            """
            UPDATE sync_jobs
            SET next_attempt_at = COALESCE(next_attempt_at, created_at, NOW())
            WHERE next_attempt_at IS NULL
            """
        )
    )
    op.alter_column(
        "sync_jobs",
        "next_attempt_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_index(
        "ix_sync_jobs_status_next_attempt_at",
        "sync_jobs",
        ["status", "next_attempt_at"],
        unique=False,
    )
    op.execute(
        sa.text(
            """
            ALTER TYPE job_type RENAME TO job_type_old
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TYPE job_type AS ENUM ('webhook', 'onboarding', 'manual_resync')
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE sync_jobs
            ALTER COLUMN job_type DROP DEFAULT,
            ALTER COLUMN job_type TYPE job_type
            USING job_type::text::job_type,
            ALTER COLUMN job_type SET DEFAULT 'webhook'
            """
        )
    )
    op.execute(
        sa.text(
            """
            DROP TYPE job_type_old
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_sync_jobs_status_next_attempt_at", table_name="sync_jobs")
    op.alter_column(
        "sync_jobs",
        "next_attempt_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.execute(
        sa.text(
            """
            ALTER TYPE job_type RENAME TO job_type_new
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TYPE job_type AS ENUM ('webhook', 'onboarding', 'manual_resync', 'scheduled_fallback')
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE sync_jobs
            ALTER COLUMN job_type DROP DEFAULT,
            ALTER COLUMN job_type TYPE job_type
            USING job_type::text::job_type,
            ALTER COLUMN job_type SET DEFAULT 'webhook'
            """
        )
    )
    op.execute(
        sa.text(
            """
            DROP TYPE job_type_new
            """
        )
    )
