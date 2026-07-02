import logging
import hashlib
import hmac
import time
from collections.abc import Callable
from typing import Any

import jwt
from plaid.model.webhook_verification_key_get_request import (
    WebhookVerificationKeyGetRequest,
)
from plaid.api.plaid_api import PlaidApi as PlaidClient

logger = logging.getLogger(__name__)


class PlaidWebhookVerificationError(Exception):
    def __init__(self, message: str, *, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.context = context or {}


class PlaidWebhookVerifier:
    def __init__(
        self,
        plaid_client: PlaidClient,
        now_fn: Callable[[], float] | None = None,
    ):
        self.plaid_client = plaid_client
        self.now_fn = now_fn or time.time
        self._key_cache: dict[str, dict[str, Any]] = {}

    def verify(self, raw_body: bytes, plaid_verification: str | None) -> None:
        if not plaid_verification:
            self._raise_verification_error("Missing Plaid-Verification header")

        try:
            header = jwt.get_unverified_header(plaid_verification)
        except jwt.PyJWTError as exc:
            self._raise_verification_error(
                "Invalid verification token",
                error=str(exc),
            )

        if header.get("alg") != "ES256":
            self._raise_verification_error(
                "Unsupported verification algorithm",
                algorithm=header.get("alg"),
            )

        key_id = header.get("kid")
        if not key_id:
            self._raise_verification_error("Missing verification key ID")

        try:
            jwk = self._get_verification_key(key_id)
        except PlaidWebhookVerificationError:
            raise
        except Exception as exc:
            self._raise_verification_error(
                "Unable to fetch Plaid verification key",
                key_id=key_id,
                error=str(exc),
            )
        key = jwt.PyJWK.from_dict(jwk).key

        try:
            claims = jwt.decode(
                plaid_verification,
                key=key,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            self._raise_verification_error(
                "Invalid webhook signature",
                key_id=key_id,
                error=str(exc),
            )

        issued_at = claims.get("iat")
        if issued_at is None:
            self._raise_verification_error(
                "Missing issued-at claim",
                key_id=key_id,
            )

        now = float(self.now_fn())
        skew_seconds = abs(now - float(issued_at))
        if skew_seconds > 300:
            self._raise_verification_error(
                "Stale verification token",
                key_id=key_id,
                issued_at=issued_at,
                now=now,
                skew_seconds=skew_seconds,
            )

        expected_hash = claims.get("request_body_sha256")
        if not expected_hash:
            self._raise_verification_error(
                "Missing request body hash",
                key_id=key_id,
            )

        actual_hash = hashlib.sha256(raw_body).hexdigest()
        if not hmac.compare_digest(actual_hash, expected_hash):
            self._raise_verification_error(
                "Webhook body hash mismatch",
                key_id=key_id,
                expected_hash=expected_hash,
                actual_hash=actual_hash,
                body_length=len(raw_body),
            )

    def _get_verification_key(self, key_id: str) -> dict[str, Any]:
        cached_key = self._key_cache.get(key_id)
        if cached_key and not self._is_expired(cached_key):
            return cached_key

        response = self.plaid_client.webhook_verification_key_get(
            WebhookVerificationKeyGetRequest(key_id=key_id)
        )
        response_dict = response.to_dict() if hasattr(response, "to_dict") else response
        key = response_dict["key"]
        self._key_cache[key_id] = key
        return key

    def _is_expired(self, jwk: dict[str, Any]) -> bool:
        expired_at = jwk.get("expired_at")
        return expired_at is not None and float(expired_at) <= self.now_fn()

    def _raise_verification_error(self, message: str, **context: Any):
        logger.warning("Plaid webhook verification failed: %s", message, extra=context)
        raise PlaidWebhookVerificationError(message, context=context)
