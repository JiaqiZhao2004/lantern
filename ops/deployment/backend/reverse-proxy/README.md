# Reverse Proxy

This component owns the local `nginx` boundary that sits between the tunnel and the backend runtime.

## Files

- [default.conf](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/reverse-proxy/default.conf)

## Responsibilities

- expose `/health/live` and `/health/ready` through the local HTTP boundary
- proxy `/api/` traffic to the backend container
- provide the loopback validation target that the tunnel depends on

## Local validation

Before testing the public tunnel hostname, verify the local origin path through `nginx`:

```bash
curl --fail --silent http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready
```

If this fails, troubleshoot the local reverse proxy or backend runtime before touching tunnel setup.
