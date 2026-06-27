# App Stack

This directory owns the backend host application stack template: `nginx`, the FastAPI backend, the transaction sync worker, Postgres, runtime env templates, and the deploy script.

## Files

- [compose.yml](./compose.yml)
- [compose.env.example](./compose.env.example)
- [backend.env.example](./backend.env.example)
- [db.env.example](./db.env.example)
- [env/public/](./env/public/)
- [env/prod/](./env/prod/)
- [deploy.sh](./deploy.sh)
- [nginx/default.conf](./nginx/default.conf)
- [postgres/create-app-role.sh](./postgres/create-app-role.sh)
- [postgres/create-app-role.sql](./postgres/create-app-role.sql)

## Environment Layout

Phase 1 runs two isolated instances of this stack on one host:

- `public` for the public app surface and Plaid Sandbox
- `prod` for the protected production runtime and Plaid Production

Each environment has its own host-local runtime files under `env/<name>/`:

- `compose.env`
- `backend.env`
- `db.env`

The checked-in `*.example` files show the intended split:

- [env/public/compose.env.example](./env/public/compose.env.example)
- [env/public/backend.env.example](./env/public/backend.env.example)
- [env/public/db.env.example](./env/public/db.env.example)
- [env/prod/compose.env.example](./env/prod/compose.env.example)
- [env/prod/backend.env.example](./env/prod/backend.env.example)
- [env/prod/db.env.example](./env/prod/db.env.example)

Keep the real runtime files on the host only; they are gitignored.

## First-Time Setup

Run these steps from `ops/deployment/backend/app-stack/` on the backend host.

1. Create host-local runtime env files for each environment if they do not already exist:

```bash
mkdir -p env/public env/prod

test -f env/public/compose.env || cp env/public/compose.env.example env/public/compose.env
test -f env/public/backend.env || cp env/public/backend.env.example env/public/backend.env
test -f env/public/db.env || cp env/public/db.env.example env/public/db.env

test -f env/prod/compose.env || cp env/prod/compose.env.example env/prod/compose.env
test -f env/prod/backend.env || cp env/prod/backend.env.example env/prod/backend.env
test -f env/prod/db.env || cp env/prod/db.env.example env/prod/db.env
```

2. Fill in the `compose.env`, `backend.env`, and `db.env` files for each environment.

Set `OBSERVABILITY_STACK_LABEL` in each `compose.env` to match the Grafana split:

- `production` for `env/prod/compose.env`
- `public` for `env/public/compose.env`

The real runtime files stay on the host and are intentionally gitignored. GHCR
authentication for private `BACKEND_IMAGE` pulls is a host-level bootstrap step
covered by [ops/bootstrap/backend-bring-up.md](../../../bootstrap/backend-bring-up.md).

After the public same-origin `/api/*` route is live, set the public Plaid webhook
registration in `env/public/backend.env` to the public app API route:

```env
PLAID_WEBHOOK_URL=https://lantern.royzhao.dev/api/v1/plaid/webhooks
```

For the protected production environment, set `env/prod/backend.env` to the
production/protected app API route you intend Plaid to call.

Do not use the protected backend origin hostname for either value; Plaid cannot
send the Cloudflare Access service-token headers that CloudFront uses for origin access.

3. Create the shared backend Docker network if it does not already exist:

```bash
docker network inspect lantern-backend >/dev/null 2>&1 || docker network create lantern-backend
```

This network is shared with the observability stack and is intentionally host-owned rather
than owned by either Compose project.

4. Place the Firebase admin credential file on the server at the path referenced by `FIREBASE_ADMIN_CREDENTIALS_PATH` for each environment.

5. Place the backend app AWS credentials file on the server at the path referenced by
`AWS_SHARED_CREDENTIALS_PATH` for each environment. The `backend` and `worker` containers mount this file
read-only at `/run/aws/credentials`, and `AWS_PROFILE` in `backend.env` selects the
profile inside it.

The KMS key and `lantern-app-kms` identity are managed by
[ops/terraform/backend-app-runtime/README.md](../../../terraform/backend-app-runtime/README.md).
Use that stack's runtime instructions to write and restrict this file.

6. Start Postgres and create the backend app role for each environment:

```bash
./postgres/create-app-role.sh public
./postgres/create-app-role.sh prod
```

The helper reads the `lantern_app` password from `DATABASE_URL` in the target
environment's `backend.env`:

```env
DATABASE_URL=postgresql+psycopg://lantern_app:<password>@db:5432/lantern
```

`postgres` is the bootstrap/admin database role. The backend should connect as
`lantern_app`, not as `postgres`. The monitoring stack uses a separate
`lantern_monitor` role.

Postgres only uses `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` the first time per environment volume. It initializes an empty data directory. Changing `db.env` later does not rename an existing database or role.

The deploy script also runs this role helper before migrations, so first deploys can
start from an empty Postgres data volume. Running the helper directly is still useful
when validating credentials before the first deploy.

## Runtime Boundary

Each Compose stack instance runs:

- `nginx`, bound to `127.0.0.1:${NGINX_BIND_PORT:-8080}`
- `backend`, the FastAPI web process
- `worker`, the transaction sync worker
- `db`, the local Postgres database

All app stack services join the external Docker network named by
`BACKEND_SHARED_NETWORK`, defaulting to `lantern-backend`, so observability can scrape the
runtime by stable per-environment DNS aliases such as `lantern-prod-backend` and
`lantern-public-nginx`. The two environments should still use distinct
Compose project names, bind ports, and Postgres volume names.

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
./deploy.sh public
./deploy.sh prod
```

The deploy script:

1. pulls runtime images
2. brings up the database if needed
3. ensures the `lantern_app` database role exists
4. creates a pre-deploy backup
5. runs Alembic migrations
6. reconciles active Plaid Item webhook URLs to `PLAID_WEBHOOK_URL`
7. updates runtime services
8. verifies readiness through `nginx`

## Manual Plaid Webhook Reconciliation

Plaid Item webhook URLs are reconciled during deploy after migrations and before
runtime rollout. To inspect or repair them manually, first ensure the database has
been bootstrapped and migrated, then run:

```bash
docker compose --env-file env/public/compose.env -f compose.yml run --rm backend \
  python -m src.plaid_webhook_reconciler --dry-run

docker compose --env-file env/public/compose.env -f compose.yml run --rm backend \
  python -m src.plaid_webhook_reconciler --apply
```

Repeat the same commands with `env/prod/compose.env` when inspecting the protected
production stack.

Deploy fails if active Plaid Items cannot be reconciled to `PLAID_WEBHOOK_URL`.

If the reconciler reports `password authentication failed for user "postgres"`,
the backend container is reading a `DATABASE_URL` that still uses the bootstrap
`postgres` role, or the existing Postgres volume was initialized with a different
`POSTGRES_PASSWORD` than the current `db.env`. The app runtime should use:

```env
DATABASE_URL=postgresql+psycopg://lantern_app:<password>@db:5432/lantern
```

Keep the bootstrap `postgres` password in `db.env`, and use
`./postgres/create-app-role.sh` to create or rotate the `lantern_app` password from
`backend.env`.

## Operational Notes

Backup runs before schema changes so recovery has a known starting point. Migrations run before rollout so the runtime contract is explicit. Rollout stops immediately if backup or migration fails, and post-rollout verification goes through `nginx`, not just directly to the backend.

Schema evolution should follow expand-contract where reasonably possible. The first production model assumes backward-compatible migrations when practical so rollout failures are survivable rather than instantly forcing destructive recovery.

Application image rollback is not treated as automatically safe after migrations. If a rollout fails after schema change, prefer fix-forward unless the documented DB recovery path is deliberately invoked.
