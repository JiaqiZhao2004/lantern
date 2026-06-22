# App Runtime

This component owns the deployed Lantern backend runtime: the Compose stack, runtime env templates, and the deploy flow.

## Files

- [compose.yml](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-runtime/compose.yml)
- [compose.env.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-runtime/compose.env.example)
- [backend.env.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-runtime/backend.env.example)
- [db.env.example](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-runtime/db.env.example)
- [deploy.sh](/Users/i-jzhao/Documents/family-finance/ops/deployment/backend/app-runtime/deploy.sh)

## Before first use

Create the real runtime files on the host:

- `cp compose.env.example compose.env`
- `cp backend.env.example backend.env`
- `cp db.env.example db.env`

The real runtime files stay on the host and are intentionally gitignored.

Place the Firebase admin credential file on the server at the path referenced by `FIREBASE_ADMIN_CREDENTIALS_PATH`.

## Deployment contract

Lantern deploys are explicit and operator-invoked. Migrations are not hidden in container startup.

Deployment order:

1. pull new images
2. bring up the database if needed
3. create a pre-deploy backup
4. run Alembic migrations
5. update runtime services
6. verify readiness through `nginx`

## Run a deploy

From `ops/deployment/backend/app-runtime/` on the server:

```bash
./deploy.sh
```

## Why this order exists

- backup runs before schema changes so recovery has a known starting point
- migrations run before rollout so the runtime contract is explicit
- rollout stops immediately if backup or migration fails
- post-rollout verification goes through `nginx`, not just directly to the backend

## Migration rule

Schema evolution should follow expand-contract where reasonably possible. The first production model assumes backward-compatible migrations when practical so rollout failures are survivable rather than instantly forcing destructive recovery.

## Rollback note

Application image rollback is not treated as automatically safe after migrations. If a rollout fails after schema change, prefer fix-forward unless the documented DB recovery path is deliberately invoked.
