# Backend Operations

This directory is reserved for steady-state backend operator workflows after successful bring-up. It mirrors the deployment component map so future runbooks can live under consistent component boundaries:

- `backend-ingress/`
- `reverse-proxy/`
- `app-runtime/`

Fresh-host and replacement-host sequencing stays in `ops/bootstrap/`. Backup and restore behavior stays in `ops/durability/backend/`.
