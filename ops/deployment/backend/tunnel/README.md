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
2. On an operator machine, install `cloudflared` if needed:

   macOS:

   ```bash
   brew install cloudflared
   cloudflared --version
   ```

   Windows PowerShell:

   ```powershell
   winget install --id Cloudflare.cloudflared
   cloudflared --version
   ```

   If Windows does not find `cloudflared` immediately after install, open a new
   PowerShell session and retry `cloudflared --version`.

3. Authenticate with Cloudflare and create the named tunnel:
   - `cloudflared tunnel login`
   - `cloudflared tunnel create lantern-backend`
4. Store the created tunnel UUID in a shell variable for the remaining steps:
   - `export TUNNEL_ID=<tunnel-uuid>`
5. Create the proxied DNS route for the ingress hostname:
   - `cloudflared tunnel route dns lantern-backend lantern-api.royzhao.dev`
6. Securely copy the generated tunnel credentials JSON file to the host under `/etc/cloudflared/`:
   - `sudo mkdir -p /etc/cloudflared`
   - `sudo cp "${TUNNEL_ID}.json" /etc/cloudflared/`
7. From `ops/deployment/backend/tunnel/`, render and install the host-local config:
   - `./render-config.sh --hostname lantern-api.royzhao.dev --tunnel-id "$TUNNEL_ID" --credentials-file "/etc/cloudflared/${TUNNEL_ID}.json" --output /tmp/cloudflared-config.yml`
   - `sudo cp /tmp/cloudflared-config.yml /etc/cloudflared/config.yml`
8. Validate the config before touching `systemd`:
   - `sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate`

After the app stack's first deploy succeeds, activate the tunnel service and complete validation.

## Activate Service

Install the systemd unit if it does not already exist, then enable and start it:

```bash
if ! systemctl cat cloudflared >/dev/null 2>&1; then
  sudo cloudflared --config /etc/cloudflared/config.yml service install
fi

sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared
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
