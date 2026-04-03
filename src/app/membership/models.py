# src/app/memberships/models.py

import uuid6
from sqlalchemy import Column, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.infrastructure.db.database import Base


class HouseholdMembership(Base):
    __tablename__ = "household_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    household_id = Column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )

    role = Column(String, nullable=False)  # e.g. admin / member / viewer

    joined_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    household = relationship("Household", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "household_id", name="uq_user_household_membership"
        ),
    )
