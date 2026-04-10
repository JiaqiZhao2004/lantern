# Persistent entities for Database ORM mapping
from src.infrastructure.db import Base
from uuid6 import uuid7
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    text,
    String,
    Text,
    Enum,
    ForeignKey,
    LargeBinary,
    DateTime,
    Numeric,
    Boolean,
    Integer,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class JobType(StrEnum):
    WEBHOOK = "webhook"
    ONBOARDING = "onboarding"
    MANUAL_RESYNC = "manual_resync"
    SCHEDULED_FALLBACK = "scheduled_fallback"


class SyncJob(Base):
    __tablename__ = "sync_jobs"
    __table_args__ = (
        Index(
            "uq_active_sync_job_per_connection",
            "institution_connection_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    # Internal ID for your own app logic
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    institution_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plaid_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_type: Mapped[str] = mapped_column(
        Enum(
            "webhook",
            "onboarding",
            "manual_resync",
            "scheduled_fallback",
            name="job_type",
        ),
        nullable=False,
        server_default="webhook",
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "queued",
            "running",
            "succeeded",
            "dead_letter",
            name="sync_status",
        ),
        nullable=False,
        server_default="queued",
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_error_type: Mapped[str | None] = mapped_column(
        Enum(
            "transient",
            "reauth_required",
            "rate_limit",
            "unknown",
            name="sync_error_type",
        ),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    institution_connection = relationship("PlaidItem", back_populates="sync_jobs")
