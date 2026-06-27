"""add account query tracking flag

Revision ID: f2a3b4c5d6e7
Revises: e2f3a4b5c6d7
Create Date: 2026-06-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "is_query_tracking_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

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

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW widget_accounts AS
            SELECT
                a.id,
                ic.household_id,
                a.name,
                a.official_name,
                a.account_type,
                a.account_subtype,
                a.current_balance,
                a.available_balance,
                a.iso_currency_code,
                a.mask
            FROM accounts a
            JOIN institution_connections ic ON ic.id = a.institution_connection_id
            WHERE a.is_active = true
              AND a.is_hidden = false
              AND a.is_query_tracking_enabled = true
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW widget_accounts AS
            SELECT
                a.id,
                ic.household_id,
                a.name,
                a.official_name,
                a.account_type,
                a.account_subtype,
                a.current_balance,
                a.available_balance,
                a.iso_currency_code,
                a.mask
            FROM accounts a
            JOIN institution_connections ic ON ic.id = a.institution_connection_id
            WHERE a.is_active = true
              AND a.is_hidden = false
            """
        )
    )

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
            WHERE t.is_removed = false
              AND t.household_id IS NOT NULL
            """
        )
    )

    op.drop_column("accounts", "is_query_tracking_enabled")
