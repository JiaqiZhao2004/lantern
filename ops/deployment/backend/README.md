# Backend Deployment

This directory is the first production deployment slice for the Lantern backend. It contains:

- `compose/` for the production app stack definition, env templates, and deploy entrypoint
- `nginx/` for the local reverse-proxy config
- `docs/` for runbooks

This slice is intentionally deployment-focused. Backend durability lives separately under `ops/durability/backend/`. Monitoring lives under `ops/observability/backend/`, and AWS durability or ingress infrastructure lives under `ops/terraform/`.

## First-pass scope

- single Ubuntu LTS host
- one shared backend image for web and worker roles
- release-triggered backend image publication to GHCR
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

- DB backups and restore docs are separate under `ops/durability/backend/`; scheduled backup automation is installed separately on the host through the checked-in `systemd` units
- tunnel and CloudFront `/api/*` routing are not wired here; that belongs to `ops/terraform/backend-ingress/`
- monitoring configuration is intentionally separate from runtime config
