# App Stack

This directory owns the backend host application stack: `nginx`, the FastAPI backend, the transaction sync worker, Postgres, runtime env templates, and the deploy script.

## Files

- [compose.yml](./compose.yml)
- [compose.env.example](./compose.env.example)
- [backend.env.example](./backend.env.example)
- [db.env.example](./db.env.example)
- [deploy.sh](./deploy.sh)
- [nginx/default.conf](./nginx/default.conf)
- [postgres/create-app-role.sh](./postgres/create-app-role.sh)
- [postgres/create-app-role.sql](./postgres/create-app-role.sql)

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

After the production same-origin `/api/*` route is live, set Plaid webhook
registration in `backend.env` to the public app API route:

```env
PLAID_WEBHOOK_URL=https://lantern.royzhao.dev/api/v1/plaid/webhooks
```

Do not use the protected backend origin hostname for this value; Plaid cannot send
the Cloudflare Access service-token headers that CloudFront uses for origin access.

Plaid Item webhook URLs are reconciled during deploy after migrations and before
runtime rollout. To inspect or repair them manually, run:

```bash
docker compose --env-file compose.env -f compose.yml run --rm backend \
  python -m src.plaid_webhook_reconciler --dry-run

docker compose --env-file compose.env -f compose.yml run --rm backend \
  python -m src.plaid_webhook_reconciler --apply
```

Deploy fails if active Plaid Items cannot be reconciled to `PLAID_WEBHOOK_URL`.

3. Create the shared backend Docker network if it does not already exist:

```bash
docker network create "${BACKEND_SHARED_NETWORK:-lantern-backend}"
```

This network is shared with the observability stack and is intentionally host-owned rather
than owned by either Compose project.

4. Place the Firebase admin credential file on the server at the path referenced by `FIREBASE_ADMIN_CREDENTIALS_PATH`.

5. Place the backend app AWS credentials file on the server at the path referenced by
`AWS_SHARED_CREDENTIALS_PATH`. The `backend` and `worker` containers mount this file
read-only at `/run/aws/credentials`, and `AWS_PROFILE` in `backend.env` selects the
profile inside it.

The KMS key and `lantern-app-kms` identity are managed by
[ops/terraform/backend-app-runtime/README.md](../../../terraform/backend-app-runtime/README.md).
Use that stack's runtime instructions to write and restrict this file.

6. Start Postgres and create the backend app role:

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
6. reconciles active Plaid Item webhook URLs to `PLAID_WEBHOOK_URL`
7. updates runtime services
8. verifies readiness through `nginx`

## Operational Notes

Backup runs before schema changes so recovery has a known starting point. Migrations run before rollout so the runtime contract is explicit. Rollout stops immediately if backup or migration fails, and post-rollout verification goes through `nginx`, not just directly to the backend.

Schema evolution should follow expand-contract where reasonably possible. The first production model assumes backward-compatible migrations when practical so rollout failures are survivable rather than instantly forcing destructive recovery.

Application image rollback is not treated as automatically safe after migrations. If a rollout fails after schema change, prefer fix-forward unless the documented DB recovery path is deliberately invoked.
