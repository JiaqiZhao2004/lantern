# Backend Host Deployment

This directory owns deployment artifacts for the Lantern backend host. It is split by lifecycle:

- [app-stack/](</Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/README.md>) owns the Compose runtime for `nginx + backend + worker + postgres`, runtime env templates, and the deploy script.
- [tunnel/](</Users/i-jzhao/Documents/family-finance/ops/deployment/backend/tunnel/README.md>) owns locally managed Cloudflare Tunnel enrollment, config rendering, and tunnel validation for `lantern-api.royzhao.dev`.

The app stack changes during application deploys and migrations. The tunnel is host ingress plumbing and should only change when the origin hostname, tunnel identity, or local origin port changes.

The cross-layer bring-up order lives in [backend-bring-up.md](/Users/i-jzhao/Documents/family-finance/ops/bootstrap/backend-bring-up.md). Backend durability lives separately under `ops/durability/backend/`. Same-origin CloudFront `/api/*` routing and Cloudflare Access backend-origin protection are owned by `ops/terraform/lantern-hosting/`.

## First-Pass Scope

- single Ubuntu LTS host
- one shared backend image for web and worker roles
- Docker Compose runtime for `nginx + backend + worker + postgres`
- locally managed Cloudflare Tunnel backend origin on `lantern-api.royzhao.dev`
- explicit deploy script with backup, migration, rollout, and health verification
- mounted Firebase admin credential file as the one runtime secret exception

## Ownership Boundaries

- DB backups, restore docs, and backup scheduling live under `ops/durability/backend/`.
- Monitoring configuration lives under `ops/observability/backend/`.
- Same-origin CloudFront `/api/*` routing and Cloudflare Access backend-origin protection live under `ops/terraform/lantern-hosting/`.

## Current Limitations

- the tunnel itself is local/script-managed for now, not Terraform-managed
- Firebase admin credentials are mounted from a host file for this first pass
