"""update plaid item sync state enum

Revision ID: 30fa3629606a
Revises: 9c0d1e2f3a4b
Create Date: 2026-04-11 19:11:31.951300

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "30fa3629606a"
down_revision: Union[str, Sequence[str], None] = "9c0d1e2f3a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_VALUES = (
    "initializing",
    "in_sync",
    "syncing",
    "failed",
)

NEW_VALUES = (
    "in_sync",
    "syncing",
    "retry_scheduled",
    "needs_reauth",
    "disabled",
)


def _create_new_enum(bind) -> None:
    new_enum = sa.Enum(*NEW_VALUES, name="plaid_item_sync_state_new")
    new_enum.create(bind, checkfirst=False)


def _create_old_enum(bind) -> None:
    old_enum = sa.Enum(*OLD_VALUES, name="plaid_item_sync_state_old")
    old_enum.create(bind, checkfirst=False)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    _create_new_enum(bind)
    op.execute(sa.text("ALTER TABLE plaid_items ALTER COLUMN sync_state DROP DEFAULT"))
    op.execute(
        sa.text(
            """
            ALTER TABLE plaid_items
            ALTER COLUMN sync_state TYPE plaid_item_sync_state_new
            USING (
                CASE sync_state::text
                    WHEN 'initializing' THEN 'syncing'
                    WHEN 'failed' THEN 'disabled'
                    ELSE sync_state::text
                END
            )::plaid_item_sync_state_new
            """
        )
    )
    op.execute(sa.text("DROP TYPE plaid_item_sync_state"))
    op.execute(
        sa.text(
            "ALTER TYPE plaid_item_sync_state_new RENAME TO plaid_item_sync_state"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE plaid_items ALTER COLUMN sync_state "
            "SET DEFAULT 'syncing'::plaid_item_sync_state"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    _create_old_enum(bind)
    op.execute(sa.text("ALTER TABLE plaid_items ALTER COLUMN sync_state DROP DEFAULT"))
    op.execute(
        sa.text(
            """
            ALTER TABLE plaid_items
            ALTER COLUMN sync_state TYPE plaid_item_sync_state_old
            USING (
                CASE sync_state::text
                    WHEN 'retry_scheduled' THEN 'failed'
                    WHEN 'needs_reauth' THEN 'failed'
                    WHEN 'disabled' THEN 'failed'
                    ELSE sync_state::text
                END
            )::plaid_item_sync_state_old
            """
        )
    )
    op.execute(sa.text("DROP TYPE plaid_item_sync_state"))
    op.execute(
        sa.text(
            "ALTER TYPE plaid_item_sync_state_old RENAME TO plaid_item_sync_state"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE plaid_items ALTER COLUMN sync_state "
            "SET DEFAULT 'initializing'::plaid_item_sync_state"
        )
    )
