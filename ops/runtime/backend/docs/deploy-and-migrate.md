# Deploy And Migrate

## Deployment contract

Lantern deploys are explicit and operator-invoked. Migrations are not hidden in container startup.

The first-pass deployment order is:

1. pull new images
2. bring up the database if needed
3. create a pre-deploy backup
4. run Alembic migrations
5. update runtime services
6. verify readiness through `nginx`

## Commands

From `ops/runtime/backend/` on the server:

```bash
./scripts/deploy.sh
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
