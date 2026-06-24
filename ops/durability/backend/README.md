# Backup And Restore

## First-pass backup posture

- logical Postgres backups
- compressed locally on the server first
- created every deploy before migrations
- automated on the host through `systemd`
- optional S3 upload through `backup.env`
- host-side local cleanup after successful runs
- retention is modeled as separate S3 prefixes:
  - `postgres/six-hourly/` for short-retention recovery points
  - `postgres/weekly/` for weekly recovery points

## Configure cloud upload

Copy `backup.env.example` to `backup.env` and fill in the S3 settings from the `ops/terraform/db-durability/` outputs.

The backup script uses the host AWS credential chain, not container credentials. Install the AWS CLI on the server and provide the backup-upload key through environment variables, `~/.aws/credentials`, or another standard AWS CLI mechanism.

`BACKUP_LOCAL_RETENTION_DAYS` controls host-side cleanup of old local backup artifacts. The default is 7 days.

## Host scheduling

The checked-in `systemd` units live under `systemd/`:

- `short-retention-backup.service`
- `short-retention-backup.timer`
- `weekly-retention-backup.service`
- `weekly-retention-backup.timer`

Install them onto the host under `/etc/systemd/system/`, then reload and enable the timers:

```bash
sudo cp systemd/*.service systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now short-retention-backup.timer
sudo systemctl enable --now weekly-retention-backup.timer
```

Enable the timers only after the backend runtime is configured and healthy enough for `backup-db.sh` to succeed. Installing the unit files earlier is fine; early timer activation is not.

The short-retention timer runs every 6 hours. The weekly-retention timer runs Sunday at `03:00` server local time. Both use `Persistent=true`, so missed runs are caught up after reboot.

Useful inspection commands:

```bash
systemctl list-timers short-retention-backup.timer weekly-retention-backup.timer
systemctl status short-retention-backup.timer weekly-retention-backup.timer
journalctl -u short-retention-backup.service -u weekly-retention-backup.service
```

Manual triggers:

```bash
sudo systemctl start short-retention-backup.service
sudo systemctl start weekly-retention-backup.service
```

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

The deploy flow does not set the weekly flag. Weekly retention comes from a separate service/timer so ordinary deploy backups do not crowd the weekly tier.

## Local cleanup

After a successful backup and any configured uploads, the script removes local files matching `postgres-*.sql.gz` that are older than `BACKUP_LOCAL_RETENTION_DAYS`.

- cleanup never runs before the current backup succeeds
- cleanup affects only local files under `backups/`
- S3 retention is still controlled independently by the bucket lifecycle rules

## Restore target

The disaster-recovery target for phase one is: restore Lantern onto a fresh Ubuntu machine from docs, image registry, env files, Firebase credential file, and database backups.

## Manual restore outline

1. provision the replacement Ubuntu host
2. install Docker and copy the deployment and durability backend subtrees
3. restore env files and the Firebase credential file
4. start only the Postgres service
5. download the chosen backup from S3 if needed:
   - `aws s3 cp s3://$BACKUP_S3_BUCKET/<chosen-object-key> /tmp/postgres-restore.sql.gz`
6. load it into Postgres:
   - `gunzip -c /tmp/postgres-restore.sql.gz | docker compose --env-file ../deployment/backend/app-stack/compose.env -f ../deployment/backend/app-stack/compose.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'`
7. run the deploy flow with the intended image tag
8. verify `/health/ready`

## Explicit limitations

- restore verification is manual first
- no automatic DB rollback is implied by deploy tooling
- backup-alerting is not part of this slice yet
