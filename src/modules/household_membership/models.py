# src/app/memberships/models.py

from datetime import datetime
import uuid

import uuid6
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.db.database import Base


class HouseholdMembership(Base):
    __tablename__ = "household_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String, nullable=False)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    household = relationship("Household", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_household_membership_single"),
        UniqueConstraint(
            "user_id", "household_id", name="uq_user_household_membership"
        ),
    )
