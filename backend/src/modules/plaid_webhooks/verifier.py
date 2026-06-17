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


class PlaidWebhookVerificationError(Exception):
    pass


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
            raise PlaidWebhookVerificationError("Missing Plaid-Verification header")

        try:
            header = jwt.get_unverified_header(plaid_verification)
        except jwt.PyJWTError as exc:
            raise PlaidWebhookVerificationError("Invalid verification token") from exc

        if header.get("alg") != "ES256":
            raise PlaidWebhookVerificationError("Unsupported verification algorithm")

        key_id = header.get("kid")
        if not key_id:
            raise PlaidWebhookVerificationError("Missing verification key ID")

        jwk = self._get_verification_key(key_id)
        key = jwt.PyJWK.from_dict(jwk).key

        try:
            claims = jwt.decode(
                plaid_verification,
                key=key,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise PlaidWebhookVerificationError("Invalid webhook signature") from exc

        issued_at = claims.get("iat")
        if issued_at is None:
            raise PlaidWebhookVerificationError("Missing issued-at claim")
        if abs(self.now_fn() - float(issued_at)) > 300:
            raise PlaidWebhookVerificationError("Stale verification token")

        expected_hash = claims.get("request_body_sha256")
        if not expected_hash:
            raise PlaidWebhookVerificationError("Missing request body hash")

        actual_hash = hashlib.sha256(raw_body).hexdigest()
        if not hmac.compare_digest(actual_hash, expected_hash):
            raise PlaidWebhookVerificationError("Webhook body hash mismatch")

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
