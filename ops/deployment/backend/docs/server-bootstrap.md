# Server Bootstrap

## Goal

Prepare a fresh Ubuntu LTS server to run the first Lantern backend deployment and durability slices.

## Baseline assumptions

- the server is a single-purpose Lantern host for now
- backend ingress will come through Cloudflare Tunnel later
- app and database ports are not exposed publicly
- runtime secrets are stored on-server outside the repo

## First-pass checklist

1. Install Docker Engine and the Docker Compose plugin.
2. Create a dedicated Lantern operations directory on the server, for example `/srv/lantern`.
3. Copy the `ops/deployment/backend/` and `ops/durability/backend/` subtrees to the server while preserving their relative layout under a shared `ops/` root, for example `/srv/lantern/ops/...`.
4. In `ops/deployment/backend/`, create the deployment env files:
   - `cp compose/compose.env.example compose/compose.env`
   - `cp compose/backend.env.example compose/backend.env`
   - `cp compose/db.env.example compose/db.env`
5. If using S3 backup upload, in `ops/durability/backend/` create the durability env file:
   - `cp backup.env.example backup.env`
6. Place the Firebase admin credential file on the server at the path referenced by `FIREBASE_ADMIN_CREDENTIALS_PATH`.
7. Authenticate the server to GHCR with a read-only token suitable for pulling Lantern images.
8. If using S3 backup upload, install the AWS CLI and place the narrow backup-upload credential on the host.
9. Pull the first backend image and verify the image tag in `compose/compose.env` is pinned by commit SHA.
10. Make the operational scripts executable:
   - `chmod +x ops/deployment/backend/compose/deploy.sh`
   - `chmod +x ops/durability/backend/backup-db.sh`
11. Bring up the database first, then run the deploy script for the full stack.

## Explicit non-goals in this runbook

- tunnel installation and CloudFront `/api/*` wiring
- automated six-hourly and weekly backup scheduling
- full monitoring stack bootstrap
- automated restore verification
