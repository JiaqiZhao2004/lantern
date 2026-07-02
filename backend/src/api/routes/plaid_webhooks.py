import json
import logging
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
from ...modules.plaid_webhooks import (
    PlaidWebhookPayload,
    PlaidWebhookService,
    PlaidWebhookVerificationError,
    PlaidWebhookVerifier,
)

# ---------- Routes ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])
logger = logging.getLogger(__name__)


def _webhook_request_log_context(
    request: Request,
    raw_body: bytes,
    plaid_verification: str | None,
) -> dict[str, object]:
    context: dict[str, object] = {
        "path": request.url.path,
        "method": request.method,
        "client_host": request.client.host if request.client else None,
        "content_type": request.headers.get("content-type"),
        "content_length": request.headers.get("content-length"),
        "user_agent": request.headers.get("user-agent"),
        "has_plaid_verification_header": plaid_verification is not None,
        "body_length": len(raw_body),
    }

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        context["body_preview"] = raw_body[:512].decode("utf-8", errors="replace")
        return context

    if isinstance(payload, dict):
        context["webhook_type"] = payload.get("webhook_type")
        context["webhook_code"] = payload.get("webhook_code")
        context["item_id"] = payload.get("item_id")
        context["environment"] = payload.get("environment")
    else:
        context["body_preview"] = str(payload)[:512]

    return context


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
        logger.warning(
            "Rejected Plaid webhook request: %s",
            exc,
            extra={
                **_webhook_request_log_context(
                    request=request,
                    raw_body=raw_body,
                    plaid_verification=plaid_verification,
                ),
                **exc.context,
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    try:
        payload = PlaidWebhookPayload.model_validate_json(raw_body)
    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        )

    with db.begin():
        webhook_service.dispatch(db=db, payload=payload)

    return Response(status_code=status.HTTP_202_ACCEPTED)
