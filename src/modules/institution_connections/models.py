from src.infrastructure.db import Base
from uuid6 import uuid7
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    String,
    Text,
    Enum,
    ForeignKey,
    LargeBinary,
    DateTime,
    Boolean,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class InstitutionConnectionStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    MEMBER_DEPARTED = "member_departed"


class InstitutionConnectionSyncState(StrEnum):
    IN_SYNC = "in_sync"
    SYNCING = "syncing"
    RETRY_SCHEDULED = "retry_scheduled"
    NEEDS_REAUTH = "needs_reauth"
    DISABLED = "disabled"


class InstitutionConnection(Base):
    __tablename__ = "institution_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "plaid_item_id", name="uq_user_plaid_item"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plaid_item_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Item ID returned by Plaid after exchanging the public_token",
    )

    institution_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    institution_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Human-readable institution name resolved from institutions/get_by_id at link time",
    )

    status: Mapped[InstitutionConnectionStatus] = mapped_column(
        Enum(
            InstitutionConnectionStatus,
            values_callable=enum_values,
            name="institution_connection_status",
        ),
        nullable=False,
        server_default=InstitutionConnectionStatus.ACTIVE,
    )

    plaid_access_token_ciphertext: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="AES-GCM ciphertext of the Plaid access_token",
    )

    plaid_access_token_nonce: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="Nonce/IV used for AES-GCM when encrypting the access_token",
    )

    plaid_access_token_encrypted_data_key: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="KMS-encrypted data key (CiphertextBlob) used to encrypt the access_token",
    )

    kms_key_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional: KMS CMK ARN or ID used to generate the data key",
    )

    transactions_cursor: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Plaid transactions sync cursor (for /transactions/sync)",
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the last successful transactions sync",
    )

    sync_state: Mapped[InstitutionConnectionSyncState] = mapped_column(
        Enum(
            InstitutionConnectionSyncState,
            values_callable=enum_values,
            name="institution_connection_sync_state",
        ),
        nullable=False,
        server_default=InstitutionConnectionSyncState.SYNCING,
        doc="Current sync lifecycle state for the institution connection",
    )

    needs_resync: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        doc="Whether the connection should be resynced from Plaid",
    )

    last_sync_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Most recent sync error message",
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

    accounts = relationship(
        "Account", back_populates="institution_connection", cascade="all, delete-orphan"
    )
    sync_jobs = relationship(
        "SyncJob",
        back_populates="institution_connection",
        cascade="all, delete-orphan",
    )


Index(
    "ix_institution_connections_user_status",
    InstitutionConnection.user_id,
    InstitutionConnection.status,
)

Index(
    "ix_institution_connections_household_status",
    InstitutionConnection.household_id,
    InstitutionConnection.status,
)
