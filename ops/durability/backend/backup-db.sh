#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_DIR="${DEPLOYMENT_DIR:-$ROOT_DIR/../../deployment/backend}"
COMPOSE_FILE="$DEPLOYMENT_DIR/compose/compose.yml"
COMPOSE_ENV="$DEPLOYMENT_DIR/compose/compose.env"
BACKUP_ENV="$ROOT_DIR/backup.env"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
BACKUP_LOCAL_RETENTION_DAYS="${BACKUP_LOCAL_RETENTION_DAYS:-7}"

if [[ -f "$BACKUP_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$BACKUP_ENV"
  set +a
fi

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
backup_path="$BACKUP_DIR/postgres-$timestamp.sql.gz"

docker compose \
  --env-file "$COMPOSE_ENV" \
  -f "$COMPOSE_FILE" \
  exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip > "$backup_path"

echo "Created local backup: $backup_path"

if [[ -n "${BACKUP_S3_BUCKET:-}" ]]; then
  if ! command -v aws >/dev/null 2>&1; then
    echo "BACKUP_S3_BUCKET is set, but the AWS CLI is not installed on this host." >&2
    exit 1
  fi

  aws_region="${BACKUP_AWS_REGION:-${AWS_REGION:-${AWS_DEFAULT_REGION:-}}}"
  if [[ -z "$aws_region" ]]; then
    echo "Set BACKUP_AWS_REGION, AWS_REGION, or AWS_DEFAULT_REGION before uploading backups to S3." >&2
    exit 1
  fi

  upload_backup() {
    local bucket="$1"
    local prefix="$2"
    local object_key
    local destination

    object_key="$(basename "$backup_path")"
    if [[ -n "$prefix" ]]; then
      object_key="$(printf '%s/%s' "${prefix%/}" "$object_key")"
    fi

    destination="s3://${bucket}/${object_key}"

    aws s3 cp \
      "$backup_path" \
      "$destination" \
      --region "$aws_region" \
      --only-show-errors

    echo "Uploaded backup to: $destination"
  }

  upload_backup "$BACKUP_S3_BUCKET" "${BACKUP_S3_PREFIX:-}"

  if [[ "${BACKUP_S3_UPLOAD_WEEKLY_COPY:-0}" == "1" ]]; then
    if [[ -z "${BACKUP_S3_WEEKLY_PREFIX:-}" ]]; then
      echo "BACKUP_S3_UPLOAD_WEEKLY_COPY=1 requires BACKUP_S3_WEEKLY_PREFIX to be set." >&2
      exit 1
    fi

    upload_backup "$BACKUP_S3_BUCKET" "$BACKUP_S3_WEEKLY_PREFIX"
  fi
fi

if [[ "$BACKUP_LOCAL_RETENTION_DAYS" =~ ^[0-9]+$ ]] && [[ "$BACKUP_LOCAL_RETENTION_DAYS" -gt 0 ]]; then
  find "$BACKUP_DIR" \
    -type f \
    -name 'postgres-*.sql.gz' \
    -mtime +"$BACKUP_LOCAL_RETENTION_DAYS" \
    -delete
  echo "Removed local backups older than ${BACKUP_LOCAL_RETENTION_DAYS} days."
fi
