from typing import Any

from pydantic import BaseModel, Field


class PlaidWebhookPayload(BaseModel):
    webhook_type: str = Field(..., description="Plaid webhook product/type.")
    webhook_code: str = Field(..., description="Plaid webhook event code.")
    item_id: str | None = Field(None, description="Plaid item_id for Item events.")
    environment: str | None = Field(None, description="Plaid environment.")
    error: dict[str, Any] | None = None
    account_id: str | None = None
