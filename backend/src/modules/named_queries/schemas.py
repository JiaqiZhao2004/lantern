import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NamedQueryCreateRequest(BaseModel):
    name: str = Field(..., description="Human-readable label for this Named Query")
    sql_query: str = Field(..., description="Flat SELECT against widget_transactions or widget_accounts")
    chart_type: str | None = Field(None, description="Opaque chart type hint for the frontend")


class NamedQueryPatchRequest(BaseModel):
    name: str | None = None
    sql_query: str | None = None
    chart_type: str | None = None


class NamedQueryPreviewRequest(BaseModel):
    sql_query: str = Field(..., description="Flat SELECT to preview without saving")


class NamedQueryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    household_id: uuid.UUID
    name: str
    sql_query: str
    referenced_columns: list[str] | None
    chart_type: str | None
    created_at: datetime
    updated_at: datetime


class ColumnMeta(BaseModel):
    name: str
    type: str


class NamedQueryDataResponse(BaseModel):
    columns: list[ColumnMeta]
    rows: list[dict[str, Any]]
    truncated: bool
