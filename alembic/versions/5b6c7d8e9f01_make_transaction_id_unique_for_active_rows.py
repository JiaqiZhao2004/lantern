"""make transaction id unique for active rows

Revision ID: 5b6c7d8e9f01
Revises: 30fa3629606a
Create Date: 2026-04-24 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b6c7d8e9f01"
down_revision: Union[str, Sequence[str], None] = "30fa3629606a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("transactions"):
        return

    op.execute(
        sa.text(
            """
            ALTER TABLE transactions
            DROP CONSTRAINT IF EXISTS transactions_plaid_transaction_id_key
            """
        )
    )
    op.execute(sa.text("DROP INDEX IF EXISTS ix_transactions_plaid_transaction_id"))

    op.create_index(
        "ix_transactions_plaid_transaction_id",
        "transactions",
        ["plaid_transaction_id"],
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
    op.drop_index("ix_transactions_plaid_transaction_id", table_name="transactions")

    op.execute(
        sa.text(
            """
            UPDATE transactions
            SET plaid_transaction_id = plaid_transaction_id || ':removed:' || id::text
            WHERE is_removed IS TRUE
            """
        )
    )
    op.create_index(
        "ix_transactions_plaid_transaction_id",
        "transactions",
        ["plaid_transaction_id"],
        unique=True,
    )
