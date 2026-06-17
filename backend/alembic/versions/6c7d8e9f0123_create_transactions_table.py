"""create transactions table

Revision ID: 6c7d8e9f0123
Revises: 5b6c7d8e9f01
Create Date: 2026-04-24 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6c7d8e9f0123"
down_revision: Union[str, Sequence[str], None] = "5b6c7d8e9f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


payment_channel = postgresql.ENUM(
    "online",
    "in store",
    "other",
    name="payment_channel",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("transactions"):
        return

    postgresql.ENUM(
        "online",
        "in store",
        "other",
        name="payment_channel",
    ).create(bind, checkfirst=True)

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plaid_transaction_id", sa.String(length=255), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_removed", sa.Boolean(), nullable=False),
        sa.Column("pending", sa.Boolean(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("authorized_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("merchant_name", sa.Text(), nullable=True),
        sa.Column("category_primary", sa.Text(), nullable=True),
        sa.Column("category_detailed", sa.Text(), nullable=True),
        sa.Column("iso_currency_code", sa.String(length=7), nullable=True),
        sa.Column("pending_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("payment_channel", payment_channel, nullable=False),
        sa.Column("check_number", sa.String(length=255), nullable=True),
        sa.Column("original_description", sa.Text(), nullable=True),
        sa.Column(
            "interbank_transfer_info",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("logo_url", sa.Text(), nullable=True),
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
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["plaid_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["plaid_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transactions_account_id",
        "transactions",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_effective_date",
        "transactions",
        ["effective_date"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_household_id",
        "transactions",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_is_removed",
        "transactions",
        ["is_removed"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_item_id",
        "transactions",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_pending_transaction_id",
        "transactions",
        ["pending_transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_plaid_transaction_id",
        "transactions",
        ["plaid_transaction_id"],
        unique=False,
    )
    op.create_index(
        "idx_transactions_household_active_effective_date",
        "transactions",
        ["household_id", "is_removed", "effective_date"],
        unique=False,
    )
    op.create_index(
        "uq_transactions_active_plaid_transaction_id",
        "transactions",
        ["plaid_transaction_id"],
        unique=True,
        postgresql_where=sa.text("is_removed IS FALSE"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("transactions"):
        return

    op.drop_index(
        "uq_transactions_active_plaid_transaction_id",
        table_name="transactions",
    )
    op.drop_index(
        "idx_transactions_household_active_effective_date",
        table_name="transactions",
    )
    op.drop_index("ix_transactions_plaid_transaction_id", table_name="transactions")
    op.drop_index("ix_transactions_pending_transaction_id", table_name="transactions")
    op.drop_index("ix_transactions_item_id", table_name="transactions")
    op.drop_index("ix_transactions_is_removed", table_name="transactions")
    op.drop_index("ix_transactions_household_id", table_name="transactions")
    op.drop_index("ix_transactions_effective_date", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_table("transactions")
    payment_channel.drop(bind, checkfirst=True)
