# Backend Host Bring-Up

This is the thin driver for bringing a Lantern backend host to a working state for either first deploy or replacement-host recovery. It coordinates other layer docs rather than duplicating them.

## Assumptions

- frontend hosting for `lantern.royzhao.dev` already exists
- the Ubuntu host already exists and you have operator SSH access
- the current target shape is the backend ingress proof slice on `lantern-api.royzhao.dev`

## Bring-up order

1. Apply the DB durability Terraform stack in [ops/terraform/db-durability/README.md](/Users/i-jzhao/Documents/family-finance/ops/terraform/db-durability/README.md).
2. Prepare host prerequisites and install host-level packages:
   - `cloudflared`
   - Docker Engine
   - Docker Compose plugin
   - AWS CLI if S3 backup upload is enabled
3. Review the reverse-proxy component in [ops/deployment/backend/reverse-proxy/README.md](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/reverse-proxy/README.md).
4. Prepare the app runtime component in [ops/deployment/backend/app-runtime/README.md](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-runtime/README.md).
5. Enroll and configure the backend ingress component in [ops/deployment/backend/backend-ingress/README.md](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/backend-ingress/README.md), but defer the local-origin and public-host validation steps until after the first backend deploy.
6. Run the first backend deploy from the `app-runtime` component.
   - After the deploy succeeds, return to the backend ingress component and complete the post-deploy validation steps.
7. Enable the backup timers described in [ops/durability/backend/README.md](/Users/i-jzhao/Documents/family-finance/ops/durability/backend/README.md) only after the backend runtime is healthy enough for backups to succeed.
8. Validate:
   - local loopback `GET /health/ready`
   - public `GET https://lantern-api.royzhao.dev/health/ready`
   - `cloudflared` survives service restart and host reboot

## Notes

- The bootstrap layer stays intentionally thin. Component-specific commands live with their components.
- The temporary ingress hostname is a proof endpoint and should be removed after same-origin `/api/*` integration is live.
