# Backend Production Roadmap

This document captures the first backend production planning pass for Lantern. It is intentionally concrete about what we are doing now, what we are deferring, and what repo-facing deliverables should exist before the backend is treated as a real production runtime.

## Target shape

- A single Ubuntu LTS personal server is the first production host.
- The host runs Docker Compose, not hand-managed processes.
- The first app runtime stack is `nginx + backend + worker + postgres`.
- The backend and worker use one shared backend image from GHCR, with different runtime commands.
- The public backend is reachable only through Cloudflare Tunnel.
- `lantern.royzhao.dev` remains the single public hostname; CloudFront `/api/*` forwarding is added only after the tunnel-backed backend is proven healthy.
- Postgres stays on the same machine at first, but durability is improved through automated logical backups uploaded to S3.
- Monitoring starts with Prometheus, Grafana, exporters, backend metrics, and a very small email-based alert set.

## Repo-facing deliverables

- `ops/runtime/backend/`
  - production Compose files
  - `nginx` config
  - env templates
  - deploy scripts
  - backend runtime docs and runbooks
- `ops/observability/backend/`
  - Prometheus config
  - Grafana provisioning
  - exporters and alert definitions
- `ops/terraform/db-durability/`
  - backup bucket
  - backup-write identity
  - retention and lifecycle policy
- `ops/terraform/backend-ingress/`
  - Cloudflare Tunnel resources
  - backend ingress DNS/routing
  - later CloudFront `/api/*` integration once the backend path is working

## Implementation order

1. Server runtime slice
   - production-oriented backend image
   - release-triggered GHCR publishing workflow for the shared backend image
   - runtime Compose stack
   - `nginx`
   - web and worker health checks
   - `/health/live` and `/health/ready` for the web app
   - explicit deploy script and runbook
2. DB durability slice
   - S3 backup bucket in `us-east-2`
   - narrow backup-upload identity
   - compressed logical Postgres backups
   - retention policy: 6-hour backups for 3 days, weekly backups for 4 weeks
   - documented restore drill target
3. Backend ingress slice
   - Terraform-managed Cloudflare Tunnel
   - backend reachable only through the tunnel
   - no public backend or Postgres ports
4. Backend monitoring slice
   - Prometheus + Grafana
   - host/container/Postgres/backend metrics
   - small alert set: backend down, Postgres down, backups missing/failing
   - email delivery first
5. Frontend/backend edge integration slice
   - CloudFront `/api/*` forwarding to the tunnel-backed backend
   - same-origin production model on `lantern.royzhao.dev`

## Operational rules

- Deploys are manual first, but must be repeatable through a checked-in script and runbook.
- The deploy script must include backup, migration, rollout, and health verification.
- If backup or migrations fail, rollout must stop immediately.
- Alembic migrations are an explicit deployment step, not hidden in container startup.
- Schema changes should follow expand-contract and aim for backward compatibility where reasonably possible.
- Images are published with immutable commit SHA tags, and the server should deploy pinned image tags rather than mutable tags.
- Backend image publication is release-triggered from GitHub Actions rather than push-triggered, so production candidate artifacts are intentional.
- Database rollback is a documented recovery operation, not an automatic deploy-script feature.

## Health model

- Web app:
  - `/health/live` answers whether the process is alive.
  - `/health/ready` answers whether the app can serve traffic, including Postgres connectivity.
- Worker:
  - start with a simpler liveness-oriented health contract
  - defer richer readiness semantics until worker behavior is better understood

## Secrets and credentials

- Most runtime configuration uses a server-side env file.
- Plaid and OpenAI secrets follow the normal env-file path.
- Firebase admin credentials remain a mounted file for the first slice.
- The mounted Firebase credential is a known operational limitation and deferred improvement area.
- Backup uploads use a narrow dedicated AWS identity; human AWS access can still use IAM Identity Center separately.
- Defer deeper server-side secret-management redesign and KMS-style host secret work for the first slice.

## Networking baseline

- No public exposure of backend or Postgres ports.
- Postgres should not be exposed outside the Docker internal network.
- `nginx` is the local ingress boundary on the machine.
- Cloudflare Tunnel is the only public app ingress path.
- Keep host hardening explicit but minimal in phase one; document what is and is not done.

## Required runbooks

- Server bootstrap
- Deploy and migrate
- Backup and restore

## Deliberate deferrals

- Managed database/runtime adoption
- Multi-machine or true high-availability topology
- Full automated restore verification
- Rich tracing or agent observability in the backend runtime slice
- Full log aggregation stack
- Automated backend production deploys
- Staging environment on the same server
- Deep host-hardening program
- Firebase credential delivery redesign
