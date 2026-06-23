# Backend Deployment

This directory contains the Lantern backend deployment components. Each component owns its own artifacts and local runbook:

- `backend-ingress/` for first-time Cloudflare Tunnel bring-up artifacts
- `edge-integration/` for CloudFront `/api/*` routing and backend-origin protection
- `reverse-proxy/` for the local `nginx` boundary
- `app-runtime/` for the Compose runtime stack and rollout flow

This stage is intentionally deployment-focused. Backend durability lives separately under `ops/durability/backend/`. The cross-layer bring-up driver lives under `ops/bootstrap/`. Future steady-state operator workflows belong under `ops/operations/backend/`.

## First-pass scope

- single Ubuntu LTS host
- one shared backend image for web and worker roles
- release-triggered backend image publication to GHCR
- Docker Compose runtime for `nginx + backend + worker + postgres`
- locally managed Cloudflare Tunnel backend origin on `lantern-api.royzhao.dev`
- explicit deploy script with backup, migration, rollout, and health verification
- mounted Firebase admin credential file as the one runtime secret exception

## Current limitations

- DB backups and restore docs are separate under `ops/durability/backend/`; scheduled backup automation is installed separately on the host through the checked-in `systemd` units
- the tunnel itself is local/script-managed for now, not Terraform-managed
- same-origin CloudFront `/api/*` integration is planned in `edge-integration/`
- monitoring configuration is intentionally separate from runtime config
