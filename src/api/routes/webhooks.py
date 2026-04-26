from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_plaid_webhook_service, get_plaid_webhook_verifier
from ...plaid.webhooks import (
    PlaidWebhookPayload,
    PlaidWebhookService,
    PlaidWebhookVerificationError,
    PlaidWebhookVerifier,
)

# ---------- Routes ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])


@router.post("/webhooks", status_code=status.HTTP_202_ACCEPTED)
async def receive_plaid_webhook(
    request: Request,
    plaid_verification: str | None = Header(default=None, alias="Plaid-Verification"),
    db: Session = Depends(get_db),
    webhook_verifier: PlaidWebhookVerifier = Depends(get_plaid_webhook_verifier),
    webhook_service: PlaidWebhookService = Depends(get_plaid_webhook_service),
):
    raw_body = await request.body()

    try:
        webhook_verifier.verify(
            raw_body=raw_body,
            plaid_verification=plaid_verification,
        )
    except PlaidWebhookVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    try:
        payload = PlaidWebhookPayload.model_validate_json(raw_body)
    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        )

    webhook_service.dispatch(db=db, payload=payload)
    return Response(status_code=status.HTTP_202_ACCEPTED)
