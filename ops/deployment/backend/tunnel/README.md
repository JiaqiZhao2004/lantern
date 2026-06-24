# Cloudflare Tunnel

This directory owns locally managed Cloudflare Tunnel enrollment, config rendering, and tunnel validation for `lantern-api.royzhao.dev`.

The tunnel has a different lifecycle from the app stack. It should only change when the tunnel identity, backend origin hostname, or local origin port changes.

## Files

- [config.yml.example](./config.yml.example)
- [render-config.sh](./render-config.sh)

## Traffic Flow

Requests to `https://lantern-api.royzhao.dev` terminate at Cloudflare's edge, travel through the outbound Cloudflare Tunnel connection maintained by `cloudflared`, then land on the app stack's local `nginx` boundary at `http://127.0.0.1:${NGINX_BIND_PORT}`.

The ingress hostname must stay proxied through Cloudflare. `DNS only` is not sufficient because there is no public backend listener to connect to directly. The host-local `nginx` process stays bound to loopback and is reachable only through the tunnel path.

## First-Time Setup

1. Install `cloudflared` on the Ubuntu host from Cloudflare's package instructions.
2. On an operator machine, authenticate with Cloudflare and create the named tunnel:
   - `cloudflared tunnel login`
   - `cloudflared tunnel create lantern-backend`
3. Store the created tunnel UUID in a shell variable for the remaining steps:
   - `export TUNNEL_ID=<tunnel-uuid>`
4. Create the proxied DNS route for the ingress hostname:
   - `cloudflared tunnel route dns lantern-backend lantern-api.royzhao.dev`
5. Securely copy the generated tunnel credentials JSON file to the host under `/etc/cloudflared/`:
   - `sudo mkdir -p /etc/cloudflared`
   - `sudo cp "${TUNNEL_ID}.json" /etc/cloudflared/`
6. From `ops/deployment/backend/tunnel/`, render and install the host-local config:
   - `./render-config.sh --hostname lantern-api.royzhao.dev --tunnel-id "$TUNNEL_ID" --credentials-file "/etc/cloudflared/${TUNNEL_ID}.json" --output /tmp/cloudflared-config.yml`
   - `sudo cp /tmp/cloudflared-config.yml /etc/cloudflared/config.yml`
7. Validate the config before touching `systemd`:
   - `sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate`

After the app stack's first deploy succeeds, activate the tunnel service and complete validation.

## Activate Service

Enable and start the packaged `cloudflared` service:

```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

## Validation

1. Validate the local app-stack origin:
   - `curl --fail --silent http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready`
2. Validate the public proof hostname before Slice 4 origin protection is enabled:
   - `curl --fail --silent https://lantern-api.royzhao.dev/health/ready`
3. Re-check after a service restart and after a host reboot.

## Not Owned Here

- app image deploys, migrations, or Postgres lifecycle
- frontend hosting
- backend CORS behavior
- Cloudflare Access, WAF rules, or rate limits
