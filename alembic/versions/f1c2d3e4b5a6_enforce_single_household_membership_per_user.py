"""enforce single household membership per user

Revision ID: f1c2d3e4b5a6
Revises: d2680e1e9f3c
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1c2d3e4b5a6"
down_revision: Union[str, Sequence[str], None] = "d2680e1e9f3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    duplicate_user_ids = bind.execute(
        sa.text(
            """
            SELECT user_id
            FROM household_memberships
            GROUP BY user_id
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicate_user_ids:
        raise RuntimeError(
            "Cannot enforce single household membership per user: "
            "existing duplicate memberships must be cleaned up first."
        )

    op.create_unique_constraint(
        "uq_user_household_membership_single",
        "household_memberships",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_user_household_membership_single",
        "household_memberships",
        type_="unique",
    )
