# Backup And Restore

## First-pass backup posture

- logical Postgres backups
- compressed locally on the server first
- created every deploy before migrations
- future S3 upload and retention policy belong to the `db-durability` slice

## Create a local backup

From `ops/runtime/backend/` on the server:

```bash
./scripts/backup-db.sh
```

This writes a timestamped compressed SQL dump under `ops/runtime/backend/backups/`.

## Restore target

The disaster-recovery target for phase one is: restore Lantern onto a fresh Ubuntu machine from docs, image registry, env files, Firebase credential file, and database backups.

## Manual restore outline

1. provision the replacement Ubuntu host
2. install Docker and copy the backend runtime subtree
3. restore env files and the Firebase credential file
4. start only the Postgres service
5. load the chosen backup into Postgres
6. run the deploy flow with the intended image tag
7. verify `/health/ready`

## Explicit limitations

- restore verification is manual first
- no automatic DB rollback is implied by deploy tooling
- backup upload to cloud storage is not implemented in this slice yet
