import hashlib
import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.utils import base64url_encode

from src.modules.plaid_webhooks.verifier import (
    PlaidWebhookVerificationError,
    PlaidWebhookVerifier,
)


class FakePlaidClient:
    def __init__(self, jwk):
        self.jwk = jwk
        self.calls = 0

    def webhook_verification_key_get(self, _):
        self.calls += 1
        return {"key": self.jwk}


def _int_to_base64url(value: int) -> str:
    return base64url_encode(value.to_bytes(32, "big")).decode("ascii")


@pytest.fixture
def signing_material():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_numbers = private_key.public_key().public_numbers()
    jwk = {
        "alg": "ES256",
        "crv": "P-256",
        "kid": "test-key",
        "kty": "EC",
        "use": "sig",
        "x": _int_to_base64url(public_numbers.x),
        "y": _int_to_base64url(public_numbers.y),
        "created_at": 1,
        "expired_at": None,
    }
    return private_key, jwk


def _signed_header(private_key, body: bytes, issued_at: int = 1_000):
    return jwt.encode(
        {
            "iat": issued_at,
            "request_body_sha256": hashlib.sha256(body).hexdigest(),
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "test-key"},
    )


def test_verify_accepts_valid_signed_payload_and_caches_key(signing_material):
    private_key, jwk = signing_material
    body = json.dumps({"webhook_type": "TRANSACTIONS"}).encode("utf-8")
    token = _signed_header(private_key=private_key, body=body)
    client = FakePlaidClient(jwk=jwk)
    verifier = PlaidWebhookVerifier(plaid_client=client, now_fn=lambda: 1_000)

    verifier.verify(raw_body=body, plaid_verification=token)
    verifier.verify(raw_body=body, plaid_verification=token)

    assert client.calls == 1


def test_verify_rejects_missing_header(signing_material):
    _, jwk = signing_material
    verifier = PlaidWebhookVerifier(
        plaid_client=FakePlaidClient(jwk=jwk),
        now_fn=lambda: 1_000,
    )

    with pytest.raises(PlaidWebhookVerificationError):
        verifier.verify(raw_body=b"{}", plaid_verification=None)


def test_verify_rejects_wrong_algorithm(signing_material):
    _, jwk = signing_material
    body = b"{}"
    token = jwt.encode(
        {"iat": 1_000, "request_body_sha256": hashlib.sha256(body).hexdigest()},
        "secret",
        algorithm="HS256",
        headers={"kid": "test-key"},
    )
    verifier = PlaidWebhookVerifier(
        plaid_client=FakePlaidClient(jwk=jwk),
        now_fn=lambda: 1_000,
    )

    with pytest.raises(PlaidWebhookVerificationError):
        verifier.verify(raw_body=body, plaid_verification=token)


def test_verify_rejects_stale_token(signing_material):
    private_key, jwk = signing_material
    body = b"{}"
    token = _signed_header(private_key=private_key, body=body, issued_at=100)
    verifier = PlaidWebhookVerifier(
        plaid_client=FakePlaidClient(jwk=jwk),
        now_fn=lambda: 1_000,
    )

    with pytest.raises(PlaidWebhookVerificationError):
        verifier.verify(raw_body=body, plaid_verification=token)


def test_verify_rejects_body_hash_mismatch(signing_material):
    private_key, jwk = signing_material
    token = _signed_header(private_key=private_key, body=b'{"ok": true}')
    verifier = PlaidWebhookVerifier(
        plaid_client=FakePlaidClient(jwk=jwk),
        now_fn=lambda: 1_000,
    )

    with pytest.raises(PlaidWebhookVerificationError):
        verifier.verify(raw_body=b'{"ok": false}', plaid_verification=token)
