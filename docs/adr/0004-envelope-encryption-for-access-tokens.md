# Envelope encryption via AWS KMS for Plaid access tokens

Plaid access tokens are stored using envelope encryption: AWS KMS generates a per-row data key, the access token is encrypted with that data key using AES-GCM, and the encrypted data key is stored alongside the ciphertext and nonce. The plaintext access token and plaintext data key are never persisted.

We chose envelope encryption over the alternatives for two reasons. Direct KMS encrypt/decrypt of every token would make every sync operation a KMS API call, adding latency and cost at scale. Application-level keys in environment variables move the secret management problem into deployment config and make key rotation painful. Envelope encryption bounds KMS calls to connection link/relink events and makes rotation tractable: re-encrypt only the data keys, not the tokens themselves.
