"""create initial user and Plaid item tables

Revision ID: 0f1e2d3c4b5a
Revises:
Create Date: 2026-02-27 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0f1e2d3c4b5a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


plaid_item_status = postgresql.ENUM(
    "active",
    "revoked",
    name="plaid_item_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    plaid_item_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("firebase_uid", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)

    op.create_table(
        "plaid_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plaid_item_id", sa.String(length=255), nullable=False),
        sa.Column("institution_id", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            plaid_item_status,
            server_default="active",
            nullable=False,
        ),
        sa.Column("access_token_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("access_token_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("access_token_encrypted_data_key", sa.LargeBinary(), nullable=False),
        sa.Column("kms_key_id", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "plaid_item_id", name="uq_user_plaid_item"),
    )
    op.create_index(
        "ix_plaid_items_plaid_item_id",
        "plaid_items",
        ["plaid_item_id"],
        unique=True,
    )
    op.create_index("ix_plaid_items_user_id", "plaid_items", ["user_id"])
    op.create_index(
        "ix_plaid_items_user_status",
        "plaid_items",
        ["user_id", "status"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_plaid_items_user_status", table_name="plaid_items")
    op.drop_index("ix_plaid_items_user_id", table_name="plaid_items")
    op.drop_index("ix_plaid_items_plaid_item_id", table_name="plaid_items")
    op.drop_table("plaid_items")

    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    plaid_item_status.drop(op.get_bind(), checkfirst=True)
