# Persistent entities for Database ORM mapping
from src.infrastructure.db import Base
from uuid6 import uuid7
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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


class PlaidAccount(Base):
    __tablename__ = "plaid_accounts"
    __table_args__ = (
        UniqueConstraint("item_id", "plaid_account_id", name="uq_item_plaid_account"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plaid_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plaid_account_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Account ID returned by Plaid",
    )

    mask: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_type: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="depository, credit, etc."
    )
    account_subtype: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="checking, savings, etc."
    )

    current_balance: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    limit_amount: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)

    iso_currency_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    unofficial_currency_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_balance_update_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner_names: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

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

    item = relationship("PlaidItem", back_populates="accounts")
