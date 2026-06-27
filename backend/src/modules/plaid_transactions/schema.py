from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionLedgerItemDTO(BaseModel):
    id: UUID = Field(..., description="Internal app UUID for this transaction row.")
    account_id: UUID = Field(..., description="Internal app UUID for the account that produced the transaction.")
    account_name: str | None = Field(None, description="Member-facing account name.")
    institution_name: str | None = Field(None, description="Institution name for the linked account.")
    occurred_at: datetime = Field(..., description="Member-facing transaction date.")
    amount: Decimal = Field(..., description="Positive for inflows, negative for outflows.")
    merchant_name: str | None = Field(None, description="Canonical Member-facing merchant label.")
    original_description: str | None = Field(None, description="Raw institution description stored for the transaction.")
    pending: bool = Field(..., description="Whether the transaction is still pending.")
    category_primary: str | None = Field(None, description="Top-level transaction category.")
    category_detailed: str | None = Field(None, description="Most specific transaction category available.")
    iso_currency_code: str | None = Field(None, description="ISO currency code when provided.")


class TransactionLedgerPageInfoDTO(BaseModel):
    next_cursor: str | None = Field(
        None,
        description="Opaque cursor for fetching the next page of results.",
    )
    has_next_page: bool = Field(..., description="Whether another page exists after this one.")
    total_count: int = Field(..., ge=0, description="Exact number of filtered transactions.")
    limit: int = Field(..., ge=1, description="Page size used for this response.")


class TransactionLedgerResponseDTO(BaseModel):
    items: list[TransactionLedgerItemDTO]
    page: TransactionLedgerPageInfoDTO


class TransactionLedgerFiltersDTO(BaseModel):
    account_ids: list[UUID] = Field(default_factory=list)
    search: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    order_by: Literal["date", "merchant", "account", "category", "amount", "pending"] = "date"
    order_direction: Literal["asc", "desc"] = "desc"
    cursor: str | None = None
    limit: int = Field(default=50, ge=1, le=100)
