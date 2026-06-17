# Persistent entities for Database ORM mapping
from src.infrastructure.db import Base
from uuid6 import uuid7
from typing import TypedDict
from datetime import datetime
from enum import StrEnum
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    Enum,
    ForeignKey,
    DateTime,
    Boolean,
    Numeric,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class InterbankTransferInfo(TypedDict, total=False):
    reference_number: str | None
    ppd_id: str | None
    payee: str | None
    by_order_of: str | None
    payer: str | None
    payment_method: str | None
    payment_processor: str | None
    reason: str | None


class PaymentChannel(StrEnum):
    ONLINE = "online"
    IN_STORE = "in store"
    OTHER = "other"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    plaid_transaction_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Transaction ID returned by Plaid",
    )

    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plaid_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plaid_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    household_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_removed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # information about the transaction itself
    pending: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
    )

    authorized_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    posted_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Plaid 'date' field (posting date)",
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="authorized_date ?? posted_date — the date the Transaction happened from the Member's perspective",
        index=True,
    )

    merchant_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category_primary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category_detailed: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    iso_currency_code: Mapped[str] = mapped_column(
        String(7),
        nullable=True,
    )

    # other more specific metadata
    pending_transaction_id: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="ID of the pending transaction that this transaction replaced",
    )

    payment_channel: Mapped[PaymentChannel] = mapped_column(
        Enum(
            PaymentChannel,
            values_callable=enum_values,
            name="payment_channel",
        ),
        nullable=False,
    )

    check_number: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    original_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    interbank_transfer_info: Mapped[InterbankTransferInfo | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Interbank transfer info from Plaid",
    )

    logo_url: Mapped[str | None] = mapped_column(
        Text,
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

    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


Index(
    "idx_transactions_household_active_occurred_at",
    "household_id",
    "is_removed",
    "occurred_at",
)

Index(
    "uq_transactions_active_plaid_transaction_id",
    Transaction.plaid_transaction_id,
    unique=True,
    postgresql_where=Transaction.is_removed.is_(False),
)
