"""add account_id to widget_transactions view

Revision ID: a9b8c7d6e5f4
Revises: f2a3b4c5d6e7
Create Date: 2026-06-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW widget_transactions AS
            SELECT
                t.id,
                t.household_id,
                t.occurred_at,
                t.amount,
                t.pending,
                t.merchant_name,
                t.category_primary,
                t.category_detailed,
                t.payment_channel,
                t.iso_currency_code,
                t.original_description,
                t.account_id
            FROM transactions t
            JOIN accounts a ON a.id = t.account_id
            WHERE t.is_removed = false
              AND t.household_id IS NOT NULL
              AND a.is_query_tracking_enabled = true
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW widget_transactions AS
            SELECT
                t.id,
                t.household_id,
                t.occurred_at,
                t.amount,
                t.pending,
                t.merchant_name,
                t.category_primary,
                t.category_detailed,
                t.payment_channel,
                t.iso_currency_code,
                t.original_description
            FROM transactions t
            JOIN accounts a ON a.id = t.account_id
            WHERE t.is_removed = false
              AND t.household_id IS NOT NULL
              AND a.is_query_tracking_enabled = true
            """
        )
    )
