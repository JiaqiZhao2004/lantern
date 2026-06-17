from src.infrastructure.db import Base
from uuid6 import uuid7
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    text,
    Text,
    Enum,
    ForeignKey,
    DateTime,
    Integer,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class SyncTrigger(StrEnum):
    WEBHOOK = "webhook"
    INITIAL_LINK = "initial_link"
    MANUAL_RESYNC = "manual_resync"


class SyncSubject(StrEnum):
    TRANSACTIONS = "transactions"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class SyncErrorType(StrEnum):
    TRANSIENT = "transient"
    REAUTH_REQUIRED = "reauth_required"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


class SyncJob(Base):
    __tablename__ = "sync_jobs"
    __table_args__ = (
        Index(
            "uq_active_sync_job_per_connection_subject",
            "institution_connection_id",
            "subject",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
        Index(
            "ix_sync_jobs_status_next_attempt_at",
            "status",
            "next_attempt_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    institution_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institution_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trigger: Mapped[SyncTrigger] = mapped_column(
        Enum(
            SyncTrigger,
            values_callable=enum_values,
            name="sync_trigger",
        ),
        nullable=False,
        server_default=SyncTrigger.WEBHOOK,
    )

    subject: Mapped[SyncSubject] = mapped_column(
        Enum(
            SyncSubject,
            values_callable=enum_values,
            name="sync_subject",
        ),
        nullable=False,
        server_default=SyncSubject.TRANSACTIONS,
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            values_callable=enum_values,
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

    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_error_type: Mapped[SyncErrorType | None] = mapped_column(
        Enum(
            SyncErrorType,
            values_callable=enum_values,
            name="sync_error_type",
        ),
        nullable=True,
    )

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

    institution_connection = relationship(
        "InstitutionConnection", back_populates="sync_jobs"
    )
