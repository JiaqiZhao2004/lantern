"""add sync jobs table

Revision ID: d40b1cadd914
Revises: e8f9a0b1c2d3
Create Date: 2026-04-09 00:26:39.741960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd40b1cadd914'
down_revision: Union[str, Sequence[str], None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


job_type = postgresql.ENUM(
    "webhook",
    "onboarding",
    "manual_resync",
    "scheduled_fallback",
    name="job_type",
    create_type=False,
)

sync_status = postgresql.ENUM(
    "queued",
    "running",
    "succeeded",
    "dead_letter",
    name="sync_status",
    create_type=False,
)

sync_error_type = postgresql.ENUM(
    "transient",
    "reauth_required",
    "rate_limit",
    "unknown",
    name="sync_error_type",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    job_type.create(op.get_bind(), checkfirst=True)
    sync_status.create(op.get_bind(), checkfirst=True)
    sync_error_type.create(op.get_bind(), checkfirst=True)

    op.create_table('sync_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_connection_id', sa.UUID(), nullable=False),
    sa.Column('job_type', job_type, server_default='webhook', nullable=False),
    sa.Column('status', sync_status, server_default='queued', nullable=False),
    sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('last_error_type', sync_error_type, nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['institution_connection_id'], ['plaid_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_jobs_institution_connection_id'), 'sync_jobs', ['institution_connection_id'], unique=False)
    op.create_index(op.f('ix_sync_jobs_status'), 'sync_jobs', ['status'], unique=False)
    op.create_index('uq_active_sync_job_per_connection', 'sync_jobs', ['institution_connection_id'], unique=True, postgresql_where=sa.text("status IN ('queued', 'running')"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_active_sync_job_per_connection', table_name='sync_jobs', postgresql_where=sa.text("status IN ('queued', 'running')"))
    op.drop_index(op.f('ix_sync_jobs_status'), table_name='sync_jobs')
    op.drop_index(op.f('ix_sync_jobs_institution_connection_id'), table_name='sync_jobs')
    op.drop_table('sync_jobs')
    sync_error_type.drop(op.get_bind(), checkfirst=True)
    sync_status.drop(op.get_bind(), checkfirst=True)
    job_type.drop(op.get_bind(), checkfirst=True)
