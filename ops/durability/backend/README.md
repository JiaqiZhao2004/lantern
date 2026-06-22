# Backup And Restore

## First-pass backup posture

- logical Postgres backups
- compressed locally on the server first
- created every deploy before migrations
- optional S3 upload through `backup.env`
- retention is modeled as separate S3 prefixes:
  - `postgres/six-hourly/` for short-retention recovery points
  - `postgres/weekly/` for weekly recovery points

## Configure cloud upload

Copy `backup.env.example` to `backup.env` and fill in the S3 settings from the `ops/terraform/db-durability/` outputs.

The backup script uses the host AWS credential chain, not container credentials. Install the AWS CLI on the server and provide the backup-upload key through environment variables, `~/.aws/credentials`, or another standard AWS CLI mechanism.

## Create a backup

From `ops/durability/backend/` on the server:

```bash
./backup-db.sh
```

This always writes a timestamped compressed SQL dump under `ops/durability/backend/backups/`.

If `BACKUP_S3_BUCKET` is configured, the same artifact is uploaded to `s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/...`.

To promote a recovery point into the weekly retention tier, run:

```bash
BACKUP_S3_UPLOAD_WEEKLY_COPY=1 ./backup-db.sh
```

The deploy flow does not set the weekly flag. Weekly retention should come from a separate operator-driven or scheduled invocation so ordinary deploy backups do not crowd the weekly tier.

## Restore target

The disaster-recovery target for phase one is: restore Lantern onto a fresh Ubuntu machine from docs, image registry, env files, Firebase credential file, and database backups.

## Manual restore outline

1. provision the replacement Ubuntu host
2. install Docker and copy the deployment and durability backend subtrees
3. restore env files and the Firebase credential file
4. start only the Postgres service
5. download the chosen backup from S3 if needed, then load it into Postgres
6. run the deploy flow with the intended image tag
7. verify `/health/ready`

## Explicit limitations

- restore verification is manual first
- no automatic DB rollback is implied by deploy tooling
- upload does not create cadence by itself; host scheduling still has to be added
