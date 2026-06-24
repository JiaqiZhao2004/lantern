# App Stack

This directory owns the backend host application stack: `nginx`, the FastAPI backend, the transaction sync worker, Postgres, runtime env templates, and the deploy script.

## Files

- [compose.yml](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/compose.yml)
- [compose.env.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/compose.env.example)
- [backend.env.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/backend.env.example)
- [db.env.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/db.env.example)
- [deploy.sh](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/deploy.sh)
- [nginx/default.conf](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/nginx/default.conf)
- [postgres/create-app-role.sh](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/postgres/create-app-role.sh)
- [postgres/create-app-role.sql](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-stack/postgres/create-app-role.sql)

## First-Time Setup

Run these steps from `ops/deployment/backend/app-stack/` on the backend host.

1. Create host-local runtime env files:

```bash
cp compose.env.example compose.env
cp backend.env.example backend.env
cp db.env.example db.env
```

2. Fill in `compose.env`, `backend.env`, and `db.env`.

The real runtime files stay on the host and are intentionally gitignored. If `BACKEND_IMAGE` points at a private GHCR image, set both `GITHUB_USERNAME` and `GHCR_TOKEN` in `compose.env`; `GHCR_TOKEN` should be a GitHub personal access token with `read:packages`.

3. Create the shared backend Docker network if it does not already exist:

```bash
docker network create "${BACKEND_SHARED_NETWORK:-lantern-backend}"
```

This network is shared with the observability stack and is intentionally host-owned rather
than owned by either Compose project.

4. Place the Firebase admin credential file on the server at the path referenced by `FIREBASE_ADMIN_CREDENTIALS_PATH`.

5. Start Postgres and create the backend app role:

```bash
./postgres/create-app-role.sh
```

The helper reads the `lantern_app` password from `DATABASE_URL` in `backend.env`:

```env
DATABASE_URL=postgresql+psycopg://lantern_app:<password>@db:5432/lantern
```

`postgres` is the bootstrap/admin database role. The backend should connect as
`lantern_app`, not as `postgres`. The monitoring stack uses a separate
`lantern_monitor` role.

Postgres only uses `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` the first time. It initializes an empty data directory. Changing `db.env` later does not rename an existing database or role.

## Runtime Boundary

The Compose stack runs:

- `nginx`, bound to `127.0.0.1:${NGINX_BIND_PORT:-8080}`
- `backend`, the FastAPI web process
- `worker`, the transaction sync worker
- `db`, the local Postgres database

All app stack services join the external Docker network named by
`BACKEND_SHARED_NETWORK`, defaulting to `lantern-backend`, so observability can scrape the
runtime by stable service names.

`nginx/default.conf` owns the local HTTP boundary between Cloudflare Tunnel and the backend service. It exposes `/health/live` and `/health/ready`, proxies `/api/` traffic to the backend container, and provides the loopback validation target that the tunnel depends on.

Validate the local origin through `nginx`:

```bash
curl --fail --silent http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready
```

If this fails, troubleshoot the local `nginx` boundary or backend runtime before touching tunnel setup.

## Deploy

Lantern deploys are explicit and operator-invoked. Migrations are not hidden in container startup.

From `ops/deployment/backend/app-stack/` on the server:

```bash
./deploy.sh
```

The deploy script:

1. authenticates Docker to GHCR when `GITHUB_USERNAME` and `GHCR_TOKEN` are set
2. pulls runtime images
3. brings up the database if needed
4. creates a pre-deploy backup
5. runs Alembic migrations
6. updates runtime services
7. verifies readiness through `nginx`

## Operational Notes

Backup runs before schema changes so recovery has a known starting point. Migrations run before rollout so the runtime contract is explicit. Rollout stops immediately if backup or migration fails, and post-rollout verification goes through `nginx`, not just directly to the backend.

Schema evolution should follow expand-contract where reasonably possible. The first production model assumes backward-compatible migrations when practical so rollout failures are survivable rather than instantly forcing destructive recovery.

Application image rollback is not treated as automatically safe after migrations. If a rollout fails after schema change, prefer fix-forward unless the documented DB recovery path is deliberately invoked.
