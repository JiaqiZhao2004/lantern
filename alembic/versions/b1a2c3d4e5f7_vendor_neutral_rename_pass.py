"""vendor-neutral rename pass: plaid_items→institution_connections, plaid_accounts→accounts,
sync job_type→trigger+subject, effective_date→occurred_at, household_id nullable

Revision ID: b1a2c3d4e5f7
Revises: 6c7d8e9f0123
Create Date: 2026-06-16 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "6c7d8e9f0123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    bind = op.get_bind()

    # -----------------------------------------------------------------------
    # 1. institution_connections  (was plaid_items)
    # -----------------------------------------------------------------------

    # New enum types for InstitutionConnection
    _exec("""
        CREATE TYPE institution_connection_status AS ENUM (
            'active', 'revoked', 'member_departed'
        )
    """)
    _exec("""
        CREATE TYPE institution_connection_sync_state AS ENUM (
            'in_sync', 'syncing', 'retry_scheduled', 'needs_reauth', 'disabled'
        )
    """)

    # Rename table
    op.rename_table("plaid_items", "institution_connections")

    # Rename access-token columns
    op.alter_column(
        "institution_connections",
        "access_token_ciphertext",
        new_column_name="plaid_access_token_ciphertext",
    )
    op.alter_column(
        "institution_connections",
        "access_token_nonce",
        new_column_name="plaid_access_token_nonce",
    )
    op.alter_column(
        "institution_connections",
        "access_token_encrypted_data_key",
        new_column_name="plaid_access_token_encrypted_data_key",
    )

    # status column: migrate from plaid_item_status enum → institution_connection_status
    # Map: active→active, revoked→revoked; any old values not present become 'revoked'
    _exec("""
        ALTER TABLE institution_connections
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE institution_connection_status
            USING CASE status::text
                WHEN 'active'  THEN 'active'::institution_connection_status
                WHEN 'revoked' THEN 'revoked'::institution_connection_status
                ELSE                 'revoked'::institution_connection_status
            END,
            ALTER COLUMN status SET DEFAULT 'active'
    """)
    _exec("DROP TYPE IF EXISTS plaid_item_status")

    # sync_state column: migrate from plaid_item_sync_state enum → institution_connection_sync_state
    _exec("""
        ALTER TABLE institution_connections
            ALTER COLUMN sync_state DROP DEFAULT,
            ALTER COLUMN sync_state TYPE institution_connection_sync_state
            USING sync_state::text::institution_connection_sync_state,
            ALTER COLUMN sync_state SET DEFAULT 'syncing'
    """)
    _exec("DROP TYPE IF EXISTS plaid_item_sync_state")

    # Rename unique constraint
    op.execute(sa.text(
        "ALTER TABLE institution_connections "
        "RENAME CONSTRAINT uq_user_plaid_item TO uq_institution_connection_user_plaid_item"
    ))

    # Rename indexes that reference the old table name
    # (PostgreSQL keeps index names table-independent so we just rename any
    #  that were created with the old table prefix)
    for old, new in [
        ("ix_plaid_items_user_id",       "ix_institution_connections_user_id"),
        ("ix_plaid_items_household_id",  "ix_institution_connections_household_id"),
        ("ix_plaid_items_plaid_item_id", "ix_institution_connections_plaid_item_id"),
    ]:
        op.execute(sa.text(f"ALTER INDEX IF EXISTS {old} RENAME TO {new}"))

    # Composite indexes used by queries (drop & recreate under new names)
    op.execute(sa.text("DROP INDEX IF EXISTS ix_plaid_items_user_status"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_plaid_items_household_status"))
    op.create_index(
        "ix_institution_connections_user_status",
        "institution_connections",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_institution_connections_household_status",
        "institution_connections",
        ["household_id", "status"],
    )

    # -----------------------------------------------------------------------
    # 2. accounts  (was plaid_accounts)
    # -----------------------------------------------------------------------

    op.rename_table("plaid_accounts", "accounts")

    # Rename FK column
    op.alter_column(
        "accounts",
        "item_id",
        new_column_name="institution_connection_id",
    )

    # Update FK constraint to point at institution_connections
    op.drop_constraint("plaid_accounts_item_id_fkey", "accounts", type_="foreignkey")
    op.create_foreign_key(
        "accounts_institution_connection_id_fkey",
        "accounts",
        "institution_connections",
        ["institution_connection_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Rename unique constraint
    op.execute(sa.text(
        "ALTER TABLE accounts "
        "RENAME CONSTRAINT uq_item_plaid_account TO uq_connection_plaid_account"
    ))

    # Rename index
    op.execute(sa.text(
        "ALTER INDEX IF EXISTS ix_plaid_accounts_item_id "
        "RENAME TO ix_accounts_institution_connection_id"
    ))

    # -----------------------------------------------------------------------
    # 3. sync_jobs  (job_type → trigger + subject; FK retarget)
    # -----------------------------------------------------------------------

    # Re-point FK from plaid_items → institution_connections
    op.drop_constraint(
        "sync_jobs_institution_connection_id_fkey", "sync_jobs", type_="foreignkey"
    )
    op.create_foreign_key(
        "sync_jobs_institution_connection_id_fkey",
        "sync_jobs",
        "institution_connections",
        ["institution_connection_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add sync_trigger enum and rename job_type column → trigger
    _exec("""
        CREATE TYPE sync_trigger AS ENUM (
            'webhook', 'initial_link', 'manual_resync'
        )
    """)
    _exec("""
        ALTER TABLE sync_jobs
            ALTER COLUMN job_type DROP DEFAULT,
            ALTER COLUMN job_type TYPE sync_trigger
            USING CASE job_type::text
                WHEN 'webhook'      THEN 'webhook'::sync_trigger
                WHEN 'onboarding'   THEN 'initial_link'::sync_trigger
                WHEN 'manual_resync' THEN 'manual_resync'::sync_trigger
                ELSE 'webhook'::sync_trigger
            END,
            ALTER COLUMN job_type SET DEFAULT 'webhook'
    """)
    _exec("DROP TYPE IF EXISTS job_type")
    op.alter_column("sync_jobs", "job_type", new_column_name="trigger")

    # Add sync_subject enum and subject column
    _exec("""
        CREATE TYPE sync_subject AS ENUM ('transactions')
    """)
    op.add_column(
        "sync_jobs",
        sa.Column(
            "subject",
            postgresql.ENUM("transactions", name="sync_subject", create_type=False),
            nullable=False,
            server_default="transactions",
        ),
    )

    # Drop old single-column unique partial index; replace with (connection_id, subject)
    op.drop_index(
        "uq_active_sync_job_per_connection",
        table_name="sync_jobs",
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.create_index(
        "uq_active_sync_job_per_connection_subject",
        "sync_jobs",
        ["institution_connection_id", "subject"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )

    # -----------------------------------------------------------------------
    # 4. transactions
    # -----------------------------------------------------------------------

    # Update FK: account_id → accounts (was plaid_accounts)
    op.drop_constraint("transactions_account_id_fkey", "transactions", type_="foreignkey")
    op.create_foreign_key(
        "transactions_account_id_fkey",
        "transactions",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update FK: item_id → institution_connections (was plaid_items)
    op.drop_constraint("transactions_item_id_fkey", "transactions", type_="foreignkey")
    op.create_foreign_key(
        "transactions_item_id_fkey",
        "transactions",
        "institution_connections",
        ["item_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # household_id: NOT NULL → nullable (SET NULL on household delete)
    op.drop_constraint("transactions_household_id_fkey", "transactions", type_="foreignkey")
    op.alter_column(
        "transactions",
        "household_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.create_foreign_key(
        "transactions_household_id_fkey",
        "transactions",
        "households",
        ["household_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # effective_date → occurred_at
    op.alter_column(
        "transactions",
        "effective_date",
        new_column_name="occurred_at",
    )

    # Update indexes that named effective_date
    op.drop_index("ix_transactions_effective_date", table_name="transactions")
    op.create_index(
        "ix_transactions_occurred_at",
        "transactions",
        ["occurred_at"],
    )

    op.drop_index(
        "idx_transactions_household_active_effective_date",
        table_name="transactions",
    )
    op.create_index(
        "idx_transactions_household_active_occurred_at",
        "transactions",
        ["household_id", "is_removed", "occurred_at"],
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # -----------------------------------------------------------------------
    # 4. transactions  (reverse)
    # -----------------------------------------------------------------------

    op.drop_index("idx_transactions_household_active_occurred_at", table_name="transactions")
    op.create_index(
        "idx_transactions_household_active_effective_date",
        "transactions",
        ["household_id", "is_removed", "occurred_at"],  # column still named occurred_at at this point
    )

    op.drop_index("ix_transactions_occurred_at", table_name="transactions")
    op.alter_column("transactions", "occurred_at", new_column_name="effective_date")
    op.create_index("ix_transactions_effective_date", "transactions", ["effective_date"])

    # household_id: back to NOT NULL (data may have NULLs — migration is lossy)
    op.drop_constraint("transactions_household_id_fkey", "transactions", type_="foreignkey")
    op.alter_column(
        "transactions",
        "household_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "transactions_household_id_fkey",
        "transactions",
        "households",
        ["household_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("transactions_item_id_fkey", "transactions", type_="foreignkey")
    op.create_foreign_key(
        "transactions_item_id_fkey",
        "transactions",
        "plaid_items",
        ["item_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("transactions_account_id_fkey", "transactions", type_="foreignkey")
    op.create_foreign_key(
        "transactions_account_id_fkey",
        "transactions",
        "plaid_accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # -----------------------------------------------------------------------
    # 3. sync_jobs  (reverse)
    # -----------------------------------------------------------------------

    op.drop_index(
        "uq_active_sync_job_per_connection_subject",
        table_name="sync_jobs",
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.create_index(
        "uq_active_sync_job_per_connection",
        "sync_jobs",
        ["institution_connection_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )

    op.drop_column("sync_jobs", "subject")
    op.execute(sa.text("DROP TYPE IF EXISTS sync_subject"))

    op.alter_column("sync_jobs", "trigger", new_column_name="job_type")
    op.execute(sa.text("""
        CREATE TYPE job_type AS ENUM ('webhook', 'onboarding', 'manual_resync')
    """))
    op.execute(sa.text("""
        ALTER TABLE sync_jobs
            ALTER COLUMN job_type DROP DEFAULT,
            ALTER COLUMN job_type TYPE job_type
            USING CASE job_type::text
                WHEN 'initial_link'  THEN 'onboarding'::job_type
                WHEN 'manual_resync' THEN 'manual_resync'::job_type
                ELSE 'webhook'::job_type
            END,
            ALTER COLUMN job_type SET DEFAULT 'webhook'
    """))
    op.execute(sa.text("DROP TYPE IF EXISTS sync_trigger"))

    op.drop_constraint(
        "sync_jobs_institution_connection_id_fkey", "sync_jobs", type_="foreignkey"
    )
    op.create_foreign_key(
        "sync_jobs_institution_connection_id_fkey",
        "sync_jobs",
        "plaid_items",
        ["institution_connection_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # -----------------------------------------------------------------------
    # 2. accounts  (reverse)
    # -----------------------------------------------------------------------

    op.execute(sa.text(
        "ALTER INDEX IF EXISTS ix_accounts_institution_connection_id "
        "RENAME TO ix_plaid_accounts_item_id"
    ))

    op.execute(sa.text(
        "ALTER TABLE accounts "
        "RENAME CONSTRAINT uq_connection_plaid_account TO uq_item_plaid_account"
    ))

    op.drop_constraint(
        "accounts_institution_connection_id_fkey", "accounts", type_="foreignkey"
    )
    op.create_foreign_key(
        "plaid_accounts_item_id_fkey",
        "accounts",
        "plaid_items",
        ["institution_connection_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column(
        "accounts",
        "institution_connection_id",
        new_column_name="item_id",
    )

    op.rename_table("accounts", "plaid_accounts")

    # -----------------------------------------------------------------------
    # 1. institution_connections  (reverse)
    # -----------------------------------------------------------------------

    op.drop_index("ix_institution_connections_household_status", table_name="institution_connections")
    op.drop_index("ix_institution_connections_user_status", table_name="institution_connections")

    for old, new in [
        ("ix_institution_connections_user_id",       "ix_plaid_items_user_id"),
        ("ix_institution_connections_household_id",  "ix_plaid_items_household_id"),
        ("ix_institution_connections_plaid_item_id", "ix_plaid_items_plaid_item_id"),
    ]:
        op.execute(sa.text(f"ALTER INDEX IF EXISTS {old} RENAME TO {new}"))

    op.execute(sa.text(
        "ALTER TABLE institution_connections "
        "RENAME CONSTRAINT uq_institution_connection_user_plaid_item TO uq_user_plaid_item"
    ))

    op.execute(sa.text("CREATE TYPE plaid_item_sync_state AS ENUM ('in_sync','syncing','retry_scheduled','needs_reauth','disabled')"))
    op.execute(sa.text("""
        ALTER TABLE institution_connections
            ALTER COLUMN sync_state DROP DEFAULT,
            ALTER COLUMN sync_state TYPE plaid_item_sync_state
            USING sync_state::text::plaid_item_sync_state,
            ALTER COLUMN sync_state SET DEFAULT 'syncing'
    """))
    op.execute(sa.text("DROP TYPE IF EXISTS institution_connection_sync_state"))

    op.execute(sa.text("CREATE TYPE plaid_item_status AS ENUM ('active','revoked')"))
    op.execute(sa.text("""
        ALTER TABLE institution_connections
            ALTER COLUMN status DROP DEFAULT,
            ALTER COLUMN status TYPE plaid_item_status
            USING CASE status::text
                WHEN 'active'  THEN 'active'::plaid_item_status
                ELSE                'revoked'::plaid_item_status
            END,
            ALTER COLUMN status SET DEFAULT 'active'
    """))
    op.execute(sa.text("DROP TYPE IF EXISTS institution_connection_status"))

    op.alter_column(
        "institution_connections",
        "plaid_access_token_encrypted_data_key",
        new_column_name="access_token_encrypted_data_key",
    )
    op.alter_column(
        "institution_connections",
        "plaid_access_token_nonce",
        new_column_name="access_token_nonce",
    )
    op.alter_column(
        "institution_connections",
        "plaid_access_token_ciphertext",
        new_column_name="access_token_ciphertext",
    )

    op.rename_table("institution_connections", "plaid_items")
