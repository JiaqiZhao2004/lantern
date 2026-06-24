# Backend Host Bring-Up

This is the thin driver for bringing a Lantern backend host to a working state for either first deploy or replacement-host recovery. It coordinates other layer docs rather than duplicating them.

## Assumptions

- frontend hosting for `lantern.royzhao.dev` already exists
- the Ubuntu host already exists and you have operator SSH access
- the `ops/` subtree is cloned or copied onto the host
- the current target shape is the backend ingress proof slice on `lantern-api.royzhao.dev`

## Bring-up order

1. Prepare host prerequisites and install host-level packages:
   - `cloudflared`
   - Docker Engine
   - Docker Compose plugin
   - AWS CLI if S3 backup upload is enabled
2. Apply the DB durability Terraform stack in [ops/terraform/db-durability/README.md](/Users/i-jzhao/Documents/family-finance/ops/terraform/db-durability/README.md).
3. Create the shared Docker network used by the app stack and observability stack:
   - `docker network create lantern-backend`
4. Enroll and configure the Cloudflare Tunnel in [ops/deployment/backend/tunnel/README.md](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/tunnel/README.md), but defer public-host validation until after the first app deploy.
5. Prepare and deploy the app stack from [ops/deployment/backend/app-stack/README.md](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/README.md).
6. Activate the `cloudflared` service and complete tunnel validation using [ops/deployment/backend/tunnel/README.md](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/tunnel/README.md).
7. Enable the backup timers described in [ops/durability/backend/README.md](/Users/i-jzhao/Documents/family-finance/ops/durability/backend/README.md) only after the backend runtime is healthy enough for backups to succeed.
8. Bring up backend observability from [ops/observability/backend/README.md](/Users/i-jzhao/Documents/family-finance/ops/observability/backend/README.md).

## Notes

- The bootstrap layer stays intentionally thin. Component-specific commands live with their components.
