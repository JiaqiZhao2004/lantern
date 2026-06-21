# Backend Runtime

This directory is the first production runtime slice for the Lantern backend. It contains:

- `compose/` for the production app stack definition and env templates
- `nginx/` for the local reverse-proxy config
- `scripts/` for repeatable operational commands
- `docs/` for runbooks

This slice is intentionally runtime-focused. Backend monitoring lives separately under `ops/observability/backend/`, and AWS durability or ingress infrastructure lives under `ops/terraform/`.

## First-pass scope

- single Ubuntu LTS host
- one shared backend image for web and worker roles
- Docker Compose runtime for `nginx + backend + worker + postgres`
- explicit deploy script with backup, migration, rollout, and health verification
- mounted Firebase admin credential file as the one runtime secret exception

## Before first use

Copy the example env files into real server-side runtime files:

- `compose/compose.env.example` -> `compose/compose.env`
- `compose/backend.env.example` -> `compose/backend.env`
- `compose/db.env.example` -> `compose/db.env`

The real runtime files are intentionally gitignored.

## Current limitations

- DB backups are created locally first; S3 upload belongs to the upcoming `ops/terraform/db-durability/` slice
- tunnel and CloudFront `/api/*` routing are not wired here; that belongs to `ops/terraform/backend-ingress/`
- monitoring configuration is intentionally separate from runtime config
