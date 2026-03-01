# features/plaid/entities.py
# Persistent entities for Database ORM mapping
from features.users.entities import User
from services.db import Base
from uuid6 import uuid7
import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Enum,
    ForeignKey,
    LargeBinary,
    DateTime,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class PlaidItemStatus(str, Enum):
    # You can also use sqlalchemy Enum directly if you prefer, but this
    # makes typing a bit nicer.
    ACTIVE = "active"
    REVOKED = "revoked"
    ERROR = "error"


class PlaidItem(Base):
    __tablename__ = "plaid_items"
    __table_args__ = (
        # One Plaid item_id should be unique, and typically you
        # also only want one row per user/item combination.
        UniqueConstraint("user_id", "plaid_item_id", name="uq_user_plaid_item"),
    )

    # Internal ID for your own app logic
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Link back to your app's user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Plaid's own identifiers
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
        doc="Plaid institution_id, if you choose to store it",
    )

    institution_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Human-readable institution name resolved from institutions/get_by_id at link time",
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "revoked",
            "error",
            name="plaid_item_status",
        ),
        nullable=False,
        server_default="active",
    )

    # ---- Encrypted access token fields (envelope encryption) ----
    #
    # access_token_plaintext is NEVER stored in DB.
    # Instead you store:
    #   - encrypted_data_key: result of KMS GenerateDataKey().CiphertextBlob
    #   - ciphertext: AES-GCM(ciphertext) of the access token using the data key
    #   - nonce: per-encryption random nonce/IV for AES-GCM
    #
    # You can also store an auth_tag separately if your AES-GCM implementation
    # returns it, or just include it in `ciphertext`.

    access_token_ciphertext: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="AES-GCM ciphertext of the Plaid access_token",
    )

    access_token_nonce: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="Nonce/IV used for AES-GCM when encrypting the access_token",
    )

    access_token_encrypted_data_key: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="KMS-encrypted data key (CiphertextBlob) used to encrypt the access_token",
    )

    # Optional: store which KMS key you used (useful if you ever have multiple)
    kms_key_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional: KMS CMK ARN or ID used to generate the data key",
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


# Optional composite index if you frequently query by (user_id, status)
Index(
    "ix_plaid_items_user_status",
    PlaidItem.user_id,
    PlaidItem.status,
)
