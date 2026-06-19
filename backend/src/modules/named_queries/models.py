import uuid
from datetime import date
from datetime import datetime

from sqlalchemy import Date, Integer, Text, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db import Base
from uuid6 import uuid7


class NamedQuery(Base):
    __tablename__ = "named_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    sql_query: Mapped[str] = mapped_column(Text, nullable=False)

    referenced_columns: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    chart_type: Mapped[str | None] = mapped_column(Text, nullable=True)

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


class NamedQueryGenerationUsage(Base):
    __tablename__ = "named_query_generation_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    quota_units_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clarifying_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repair_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "usage_date",
            name="uq_named_query_generation_usage_household_date",
        ),
    )
