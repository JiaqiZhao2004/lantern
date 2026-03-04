"""add sync columns to plaid_items and create plaid_accounts

Revision ID: a1b2c3d4e5f6
Revises: 48a22a87c5de
Create Date: 2026-03-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "48a22a87c5de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- plaid_items: new sync columns ---
    op.add_column(
        "plaid_items",
        sa.Column("transactions_cursor", sa.Text(), nullable=True),
    )
    op.add_column(
        "plaid_items",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- plaid_accounts table ---
    op.create_table(
        "plaid_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plaid_account_id", sa.Text(), nullable=False),
        sa.Column("mask", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("official_name", sa.Text(), nullable=True),
        sa.Column("account_type", sa.Text(), nullable=True),
        sa.Column("account_subtype", sa.Text(), nullable=True),
        sa.Column("current_balance", sa.Numeric(), nullable=True),
        sa.Column("available_balance", sa.Numeric(), nullable=True),
        sa.Column("limit_amount", sa.Numeric(), nullable=True),
        sa.Column("iso_currency_code", sa.Text(), nullable=True),
        sa.Column("unofficial_currency_code", sa.Text(), nullable=True),
        sa.Column("last_balance_update_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "owner_names", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_hidden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["plaid_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "item_id", "plaid_account_id", name="uq_item_plaid_account"
        ),
    )
    op.create_index("ix_plaid_accounts_item_id", "plaid_accounts", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_plaid_accounts_item_id", table_name="plaid_accounts")
    op.drop_table("plaid_accounts")

    op.drop_column("plaid_items", "last_synced_at")
    op.drop_column("plaid_items", "transactions_cursor")
