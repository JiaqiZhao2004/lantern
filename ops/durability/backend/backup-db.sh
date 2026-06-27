#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_ENV="${APP_STACK_ENV:-${1:-prod}}"
if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [public|prod|<env-name>]" >&2
  exit 1
fi

DEPLOYMENT_DIR="${DEPLOYMENT_DIR:-$ROOT_DIR/../../deployment/backend/app-stack}"
ENV_DIR="$DEPLOYMENT_DIR/env/$TARGET_ENV"
COMPOSE_FILE="$DEPLOYMENT_DIR/compose.yml"
COMPOSE_ENV="$ENV_DIR/compose.env"
BACKUP_ENV="$ROOT_DIR/backup.env"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
BACKUP_LOCAL_RETENTION_DAYS="${BACKUP_LOCAL_RETENTION_DAYS:-7}"
BACKUP_TIER="${BACKUP_TIER:-six-hourly}"

if [[ ! -d "$ENV_DIR" ]]; then
  echo "Missing environment directory: $ENV_DIR" >&2
  exit 1
fi

if [[ -f "$BACKUP_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$BACKUP_ENV"
  set +a
fi

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
started_at_epoch="$(date +%s)"
backup_path="$BACKUP_DIR/${TARGET_ENV}-postgres-$timestamp.sql.gz"

write_prom_marker() {
  local tier="$1"
  local stage="$2"
  local succeeded_at_epoch="$3"
  local duration_seconds="$4"
  local size_bytes="$5"

  if [[ -z "${BACKUP_PROM_TEXTFILE_DIR:-}" ]]; then
    return 0
  fi

  mkdir -p "$BACKUP_PROM_TEXTFILE_DIR"

  local marker_path="$BACKUP_PROM_TEXTFILE_DIR/lantern-backup-${TARGET_ENV}-${tier}-${stage}.prom"
  local tmp_path="${marker_path}.$$"

  {
    printf 'lantern_backup_last_success_timestamp_seconds{environment="%s",tier="%s",stage="%s"} %s\n' "$TARGET_ENV" "$tier" "$stage" "$succeeded_at_epoch"
    printf 'lantern_backup_last_success_duration_seconds{environment="%s",tier="%s",stage="%s"} %s\n' "$TARGET_ENV" "$tier" "$stage" "$duration_seconds"
    printf 'lantern_backup_last_success_size_bytes{environment="%s",tier="%s",stage="%s"} %s\n' "$TARGET_ENV" "$tier" "$stage" "$size_bytes"
  } > "$tmp_path"

  mv "$tmp_path" "$marker_path"
}

docker compose \
  --env-file "$COMPOSE_ENV" \
  -f "$COMPOSE_FILE" \
  exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip > "$backup_path"

echo "Created local backup: $backup_path"

completed_at_epoch="$(date +%s)"
backup_size_bytes="$(wc -c < "$backup_path" | tr -d ' ')"
write_prom_marker "$BACKUP_TIER" "local" "$completed_at_epoch" "$((completed_at_epoch - started_at_epoch))" "$backup_size_bytes"

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

  aws_command=(aws)
  if [[ -n "${BACKUP_AWS_PROFILE:-}" ]]; then
    aws_command+=(--profile "$BACKUP_AWS_PROFILE")
  fi

  upload_backup() {
    local bucket="$1"
    local prefix="$2"
    local tier="$3"
    local object_key
    local destination
    local upload_started_at_epoch
    local upload_completed_at_epoch

    object_key="$(basename "$backup_path")"
    if [[ -n "$prefix" ]]; then
      object_key="$(printf '%s/%s' "${prefix%/}" "$object_key")"
    fi

    destination="s3://${bucket}/${object_key}"

    upload_started_at_epoch="$(date +%s)"
    "${aws_command[@]}" s3 cp \
      "$backup_path" \
      "$destination" \
      --region "$aws_region" \
      --only-show-errors

    echo "Uploaded backup to: $destination"
    upload_completed_at_epoch="$(date +%s)"
    write_prom_marker "$tier" "s3" "$upload_completed_at_epoch" "$((upload_completed_at_epoch - upload_started_at_epoch))" "$backup_size_bytes"
  }

  upload_backup "$BACKUP_S3_BUCKET" "${BACKUP_S3_PREFIX:-}" "six-hourly"

  if [[ "${BACKUP_S3_UPLOAD_WEEKLY_COPY:-0}" == "1" ]]; then
    if [[ -z "${BACKUP_S3_WEEKLY_PREFIX:-}" ]]; then
      echo "BACKUP_S3_UPLOAD_WEEKLY_COPY=1 requires BACKUP_S3_WEEKLY_PREFIX to be set." >&2
      exit 1
    fi

    upload_backup "$BACKUP_S3_BUCKET" "$BACKUP_S3_WEEKLY_PREFIX" "weekly"
  fi
fi

if [[ "$BACKUP_LOCAL_RETENTION_DAYS" =~ ^[0-9]+$ ]] && [[ "$BACKUP_LOCAL_RETENTION_DAYS" -gt 0 ]]; then
  find "$BACKUP_DIR" \
    -type f \
    -name "${TARGET_ENV}-postgres-*.sql.gz" \
    -mtime +"$BACKUP_LOCAL_RETENTION_DAYS" \
    -delete
  echo "Removed local backups older than ${BACKUP_LOCAL_RETENTION_DAYS} days."
fi
