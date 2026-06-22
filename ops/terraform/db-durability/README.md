# Lantern DB Durability Terraform

This stack provisions the AWS durability boundary for Lantern's first production database posture:

- a private S3 bucket for logical Postgres backups
- server-side encryption and blocked public access
- lifecycle rules for short-retention and weekly-retention backup prefixes
- a narrow IAM user that can upload backups into those prefixes

The current runtime model uploads compressed `pg_dump` artifacts from the Ubuntu host. Terraform creates the bucket and upload identity; host-side scheduling remains a separate operational step.

## Retention model

S3 lifecycle policies can expire objects by age, but they do not create weekly snapshots for us. To match the roadmap's recovery-point model, this stack treats retention as two prefixes in one bucket:

- `postgres/six-hourly/` expires after 3 days
- `postgres/weekly/` expires after 28 days

The runtime backup script uploads every backup into the short-retention prefix by default. Weekly retention comes from a separate invocation that also copies the artifact into the weekly prefix.

## State backend

Terraform state is stored in the existing shared S3 bucket:

- bucket: `terraform-state-royzhao`
- key: `lantern/db-durability/terraform.tfstate`
- region: `us-east-2`

## Prerequisites

Use your usual AWS credentials locally, for example through `AWS_PROFILE`, `aws sso login`, or environment variables.

## Apply

```bash
cd ops/terraform/db-durability
terraform init
terraform plan
terraform apply
```

## Runtime values

After apply, wire these values into `ops/durability/backend/backup.env` on the server:

- `BACKUP_AWS_REGION`
- `BACKUP_S3_BUCKET`
- `BACKUP_S3_PREFIX=postgres/six-hourly`
- `BACKUP_S3_WEEKLY_PREFIX=postgres/weekly`

Create or export the AWS credential from these outputs:

```bash
terraform output -raw backup_upload_access_key_id
terraform output -raw backup_upload_secret_access_key
```

Keep the secret outside the repo and install it on the host with the rest of the runtime credentials.
