# Backend Ingress

This component handles first-time backend ingress bring-up for the temporary proof hostname `lantern-api.royzhao.dev`.

## What this component owns

- locally managed Cloudflare Tunnel enrollment
- the host-local `cloudflared` config shape
- the helper script for rendering a local config file
- first-time validation of the public tunnel path

## Why this is local for now

Slice 3 intentionally uses a locally managed tunnel instead of Terraform-managed ingress resources. The documented Cloudflare local-management flow is clearer for first enrollment and host credential handling, and it avoids pushing tunnel secret material or awkward enrollment steps into Terraform just to force this proof endpoint into infra-as-code.

## How the traffic flows

Requests to `https://lantern-api.royzhao.dev` terminate at Cloudflare's edge, then travel through the outbound Cloudflare Tunnel connection maintained by `cloudflared`, then land on the local reverse proxy at `http://127.0.0.1:${NGINX_BIND_PORT}`.

The proof hostname must stay proxied through Cloudflare. `DNS only` is not sufficient here because there is no public backend listener to connect to directly. The host-local `nginx` process stays bound to loopback and is reachable only through the tunnel path.

## Files

- [config.yml.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/backend-ingress/config.yml.example)
- [render-config.sh](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/backend-ingress/render-config.sh)

## Pre-deploy ingress setup

1. Install `cloudflared` on the Ubuntu host from Cloudflare's package instructions.
2. On an operator machine, authenticate with Cloudflare and create the named tunnel for Lantern:
   - `cloudflared tunnel login`
   - `cloudflared tunnel create lantern-backend`
3. Create the proxied DNS route for the proof hostname:
   - `cloudflared tunnel route dns lantern-backend lantern-api.royzhao.dev`
4. Securely copy the generated tunnel credentials JSON file to the host under `/etc/cloudflared/`:
   - `sudo mkdir -p /etc/cloudflared`
   - `sudo cp <tunnel-uuid>.json /etc/cloudflared/`
5. Render a host-local config file from the checked-in template:
   - `./render-config.sh --hostname lantern-api.royzhao.dev --tunnel-id <tunnel-uuid> --credentials-file /etc/cloudflared/<tunnel-uuid>.json --output /tmp/cloudflared-config.yml`
   - `sudo cp /tmp/cloudflared-config.yml /etc/cloudflared/config.yml`
6. Validate the config before touching `systemd`:
   - `sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate`

After step 6, return to [backend-host-bring-up.md](/Users/i-jzhao/Documents/family-finance/ops/bootstrap/backend-host-bring-up.md:1) and complete the first backend deploy from the `app-runtime` component before continuing here.

## Post-deploy ingress validation

7. Validate the local origin before public tunnel testing:
   - `curl --fail --silent http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready`
8. On the Ubuntu backend host, enable and start the packaged `cloudflared` service:
   - `sudo systemctl enable cloudflared`
   - `sudo systemctl start cloudflared`
   - `sudo systemctl status cloudflared`
9. Validate the public proof hostname:
   - `curl --fail --silent https://lantern-api.royzhao.dev/health/ready`
10. Re-check after a service restart and after a host reboot.

## What this component does not do

- install the host itself
- provision the frontend hosting stack
- change backend CORS behavior
- add Cloudflare Access, WAF rules, or rate limits for this proof slice
- validate a Firebase-authenticated API flow as part of mandatory slice acceptance
