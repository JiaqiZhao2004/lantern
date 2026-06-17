"""add named_queries table and widget views

Revision ID: c1d2e3f4a5b6
Revises: b1a2c3d4e5f7
Create Date: 2026-06-17 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b1a2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Stable views — public API contract for Named Query SQL
    # ------------------------------------------------------------------
    op.execute(sa.text("""
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
    """))

    op.execute(sa.text("""
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
    """))

    # ------------------------------------------------------------------
    # 2. named_queries table
    # ------------------------------------------------------------------
    op.create_table(
        "named_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("sql_query", sa.Text(), nullable=False),
        sa.Column("referenced_columns", postgresql.JSONB(), nullable=True),
        sa.Column("chart_type", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_named_queries_household_id", "named_queries", ["household_id"])


def downgrade() -> None:
    # Destructive — all Named Query rows are lost on rollback.
    # Ensure DB backups exist before running this in production.
    op.execute(sa.text("DELETE FROM named_queries"))
    op.drop_index("ix_named_queries_household_id", table_name="named_queries")
    op.drop_table("named_queries")
    op.execute(sa.text("DROP VIEW IF EXISTS widget_accounts"))
    op.execute(sa.text("DROP VIEW IF EXISTS widget_transactions"))
