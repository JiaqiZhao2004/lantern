"""add last_sync_error to plaid_items

Revision ID: d7e8f9a0b1c2
Revises: c4d5e6f7a8b9
Create Date: 2026-04-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "plaid_items",
        sa.Column("last_sync_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plaid_items", "last_sync_error")
