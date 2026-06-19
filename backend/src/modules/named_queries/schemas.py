import uuid
from datetime import datetime
from typing import Any, Literal

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


class NamedQueryGenerationMessage(BaseModel):
    role: Literal["member", "assistant"]
    content: str = Field(..., min_length=1)


class NamedQueryGenerateRequest(BaseModel):
    messages: list[NamedQueryGenerationMessage] = Field(..., min_length=1)


class NamedQueryCandidate(BaseModel):
    sql_query: str
    chart_type: str | None = None


class NamedQueryClarifyingQuestionResponse(BaseModel):
    type: Literal["clarifying_question"] = "clarifying_question"
    question: str


class NamedQueryCandidateResponse(BaseModel):
    type: Literal["named_query_candidate"] = "named_query_candidate"
    name: str
    candidate: NamedQueryCandidate


class NamedQueryGenerationFailureResponse(BaseModel):
    type: Literal["generation_failure"] = "generation_failure"
    message: str
    reason: (
        Literal[
            "provider_quota_exceeded",
            "provider_not_configured",
            "provider_unavailable",
        ]
        | None
    ) = None


NamedQueryGenerateResponse = (
    NamedQueryClarifyingQuestionResponse
    | NamedQueryCandidateResponse
    | NamedQueryGenerationFailureResponse
)


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
