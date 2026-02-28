import os

import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AWS_REGION = os.getenv("AWS_REGION")
KMS_KEY_ID = os.getenv("KMS_KEY_ID")
if not KMS_KEY_ID:
    raise ValueError("KMS_KEY_ID environment variable is not set")
if not AWS_REGION:
    raise ValueError("AWS_REGION environment variable is not set")

_kms_client = None


def _get_kms_client():
    global _kms_client
    if _kms_client is None:
        _kms_client = boto3.client("kms", region_name=AWS_REGION)
    return _kms_client


def encrypt_secret(
    plaintext: str,
    kms_key_id: str = KMS_KEY_ID,
) -> tuple[bytes, bytes, bytes]:
    """
    Encrypts a plaintext string using KMS envelope encryption with AES-256-GCM.

    Workflow:
      1. Ask KMS to generate a 256-bit data key.
         KMS returns two forms of the same key:
           - Plaintext  → used in-memory to encrypt; NEVER stored.
           - CiphertextBlob → stored in DB; only KMS can decrypt it.
      2. Encrypt the plaintext with AES-256-GCM using the Plaintext data key.
      3. Discard the Plaintext data key from memory after use.

    Returns:
        ciphertext (bytes)           – AES-GCM encrypted secret (includes GCM auth tag)
        nonce      (bytes)           – 12-byte random nonce/IV used for this encryption
        encrypted_data_key (bytes)   – KMS CiphertextBlob; store alongside ciphertext
    """
    kms = _get_kms_client()

    # Step 1: generate a fresh data key from KMS
    response = kms.generate_data_key(KeyId=kms_key_id, KeySpec="AES_256")
    plaintext_data_key: bytes = response[
        "Plaintext"
    ]  # raw 32-byte key – in-memory only
    encrypted_data_key: bytes = response["CiphertextBlob"]  # persisted in DB

    # Step 2: AES-256-GCM encrypt
    nonce = os.urandom(12)  # 96-bit nonce; unique per encryption
    ciphertext = AESGCM(plaintext_data_key).encrypt(
        nonce, plaintext.encode("utf-8"), None
    )

    return ciphertext, nonce, encrypted_data_key


def decrypt_secret(
    encrypted_data_key: bytes,
    nonce: bytes,
    ciphertext: bytes,
) -> str:
    """
    Decrypts a ciphertext produced by encrypt_secret.

    Workflow:
      1. Ask KMS to decrypt the CiphertextBlob back to the raw data key.
      2. Use the raw data key to AES-256-GCM decrypt the ciphertext.

    Returns:
        plaintext (str) – the original secret string
    """
    kms = _get_kms_client()

    # Step 1: recover the data key from KMS
    response = kms.decrypt(CiphertextBlob=encrypted_data_key)
    plaintext_data_key: bytes = response["Plaintext"]

    # Step 2: AES-256-GCM decrypt (also verifies the GCM auth tag)
    plaintext_bytes = AESGCM(plaintext_data_key).decrypt(nonce, ciphertext, None)

    return plaintext_bytes.decode("utf-8")
