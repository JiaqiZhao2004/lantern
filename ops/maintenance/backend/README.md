# Backend Operations

This directory is reserved for steady-state backend operator workflows after successful bring-up. Future runbooks should follow the backend host deployment lifecycle boundaries:

- `app-stack/` for app deploys, migrations, runtime services, and the local `nginx` boundary
- `tunnel/` for Cloudflare Tunnel operations

Fresh-host and replacement-host sequencing stays in `ops/bootstrap/`. Backup and restore behavior stays in `ops/durability/backend/`. Backend host deployment artifacts live under `ops/deployment/backend/`.
