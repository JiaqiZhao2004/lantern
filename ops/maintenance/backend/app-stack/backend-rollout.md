# Backend Rollout

Use this runbook to roll out a new backend image on the backend host.

`ops/deployment/backend/app-stack/deploy.sh` is sufficient for the normal
single-host backend rollout path. It pulls the configured image, starts Postgres if
needed, ensures the app DB role exists, creates a pre-deploy database backup, runs
Alembic migrations, reconciles Plaid webhook URLs, updates `nginx`, `backend`, and
`worker`, and verifies readiness through the local `nginx` boundary.

## Preconditions

- You are on the backend host.
- Docker can pull the image referenced by `BACKEND_IMAGE`.
- `ops/deployment/backend/app-stack/compose.env`, `backend.env`, and `db.env`
  are present and current.
- `BACKEND_IMAGE` in `compose.env` points at the new backend image tag.
- The shared Docker network named by `BACKEND_SHARED_NETWORK` exists.
- The Firebase and AWS credential files referenced by `compose.env` exist.
- `ops/durability/backend/backup-db.sh` is executable and the backup destination
  is healthy.

## Rollout

From `ops/deployment/backend/app-stack/`:

```bash
./deploy.sh
```

The script stops at the first failed step. If it completes, it has already checked:

- migrations completed
- Plaid webhook reconciliation completed
- `nginx`, `backend`, and `worker` were started with Compose health waiting
- `http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready` returned success

## Aftercare

Inspect runtime state:

```bash
docker compose --env-file compose.env -f compose.yml ps nginx backend worker db
```

If the rollout fails before runtime services are updated, fix the failing
precondition and rerun `./deploy.sh`.

If it fails after migrations, prefer a fix-forward deploy. Application image
rollback is not automatically safe once schema changes have run. Use the database
restore workflow in `ops/durability/backend/` only when deliberately choosing
database recovery.
