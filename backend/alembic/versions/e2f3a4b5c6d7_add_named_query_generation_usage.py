"""add named query generation usage

Revision ID: e2f3a4b5c6d7
Revises: c1d2e3f4a5b6
Create Date: 2026-06-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "named_query_generation_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "household_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("quota_units_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("llm_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clarifying_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repair_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generation_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_failures", sa.Integer(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint(
            "household_id",
            "usage_date",
            name="uq_named_query_generation_usage_household_date",
        ),
    )
    op.create_index(
        "ix_named_query_generation_usage_household_id",
        "named_query_generation_usage",
        ["household_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_named_query_generation_usage_household_id",
        table_name="named_query_generation_usage",
    )
    op.drop_table("named_query_generation_usage")
