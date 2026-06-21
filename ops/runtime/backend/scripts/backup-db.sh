#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/compose/compose.yml"
COMPOSE_ENV="$ROOT_DIR/compose/compose.env"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
backup_path="$BACKUP_DIR/postgres-$timestamp.sql.gz"

docker compose \
  --env-file "$COMPOSE_ENV" \
  -f "$COMPOSE_FILE" \
  exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip > "$backup_path"

echo "Created local backup: $backup_path"
