"""add household_id to plaid_items

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-04-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("plaid_items", sa.Column("household_id", sa.UUID(), nullable=True))

    bind.execute(
        sa.text(
            """
            UPDATE plaid_items AS pi
            SET household_id = hm.household_id
            FROM household_memberships AS hm
            WHERE hm.user_id = pi.user_id
            """
        )
    )

    missing_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM plaid_items
            WHERE household_id IS NULL
            """
        )
    ).scalar_one()

    if missing_count:
        raise RuntimeError(
            "Cannot add required plaid_items.household_id: "
            "one or more existing Plaid items do not map to a household membership."
        )

    op.create_foreign_key(
        "fk_plaid_items_household_id_households",
        "plaid_items",
        "households",
        ["household_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_plaid_items_household_id",
        "plaid_items",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        "ix_plaid_items_household_status",
        "plaid_items",
        ["household_id", "status"],
        unique=False,
    )
    op.alter_column("plaid_items", "household_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_plaid_items_household_status", table_name="plaid_items")
    op.drop_index("ix_plaid_items_household_id", table_name="plaid_items")
    op.drop_constraint(
        "fk_plaid_items_household_id_households",
        "plaid_items",
        type_="foreignkey",
    )
    op.drop_column("plaid_items", "household_id")
