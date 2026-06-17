"""add sync_state and needs_resync to plaid_items

Revision ID: c4d5e6f7a8b9
Revises: f1c2d3e4b5a6
Create Date: 2026-04-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "f1c2d3e4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


plaid_item_sync_state = sa.Enum(
    "initializing",
    "in_sync",
    "syncing",
    "failed",
    name="plaid_item_sync_state",
)


def upgrade() -> None:
    plaid_item_sync_state.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "plaid_items",
        sa.Column(
            "sync_state",
            plaid_item_sync_state,
            nullable=False,
            server_default="initializing",
        ),
    )
    op.add_column(
        "plaid_items",
        sa.Column(
            "needs_resync",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("plaid_items", "needs_resync")
    op.drop_column("plaid_items", "sync_state")
    plaid_item_sync_state.drop(op.get_bind(), checkfirst=True)
