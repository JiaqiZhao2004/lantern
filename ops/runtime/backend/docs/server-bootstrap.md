# Server Bootstrap

## Goal

Prepare a fresh Ubuntu LTS server to run the first Lantern backend runtime slice.

## Baseline assumptions

- the server is a single-purpose Lantern host for now
- backend ingress will come through Cloudflare Tunnel later
- app and database ports are not exposed publicly
- runtime secrets are stored on-server outside the repo

## First-pass checklist

1. Install Docker Engine and the Docker Compose plugin.
2. Create a dedicated Lantern runtime directory on the server, for example `/srv/lantern`.
3. Copy the `ops/runtime/backend/` subtree to the server.
4. Create the env files:
   - `cp compose/compose.env.example compose/compose.env`
   - `cp compose/backend.env.example compose/backend.env`
   - `cp compose/db.env.example compose/db.env`
5. Place the Firebase admin credential file on the server at the path referenced by `FIREBASE_ADMIN_CREDENTIALS_PATH`.
6. Authenticate the server to GHCR with a read-only token suitable for pulling Lantern images.
7. Pull the first backend image and verify the image tag in `compose/compose.env` is pinned by commit SHA.
8. Make the operational scripts executable:
   - `chmod +x scripts/*.sh`
9. Bring up the database first, then run the deploy script for the full stack.

## Explicit non-goals in this runbook

- tunnel installation and CloudFront `/api/*` wiring
- S3 backup upload plumbing
- full monitoring stack bootstrap
- automated restore verification
