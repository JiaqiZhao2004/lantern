#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/compose.yml"
COMPOSE_ENV="$ROOT_DIR/compose.env"
BACKEND_ENV="$ROOT_DIR/backend.env"
DB_ENV="$ROOT_DIR/db.env"
DURABILITY_DIR="${DURABILITY_DIR:-$ROOT_DIR/../../../durability/backend}"
BACKUP_SCRIPT="$DURABILITY_DIR/backup-db.sh"

for required_file in "$COMPOSE_ENV" "$BACKEND_ENV" "$DB_ENV"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Missing required file: $required_file" >&2
    exit 1
  fi
done

set -a
# shellcheck disable=SC1090
source "$COMPOSE_ENV"
set +a

BACKEND_SHARED_NETWORK="${BACKEND_SHARED_NETWORK:-lantern-backend}"

if [[ ! -x "$BACKUP_SCRIPT" ]]; then
  echo "Missing executable backup script: $BACKUP_SCRIPT" >&2
  exit 1
fi

if ! docker network inspect "$BACKEND_SHARED_NETWORK" >/dev/null 2>&1; then
  echo "Missing Docker network: $BACKEND_SHARED_NETWORK" >&2
  echo "Create it before deploy: docker network create $BACKEND_SHARED_NETWORK" >&2
  exit 1
fi

compose() {
  docker compose --env-file "$COMPOSE_ENV" -f "$COMPOSE_FILE" "$@"
}

if [[ -n "${GITHUB_USERNAME:-}" || -n "${GHCR_TOKEN:-}" ]]; then
  if [[ -z "${GITHUB_USERNAME:-}" || -z "${GHCR_TOKEN:-}" ]]; then
    echo "Set both GITHUB_USERNAME and GHCR_TOKEN in compose.env to authenticate to GHCR." >&2
    exit 1
  fi

  echo "Authenticating Docker to ghcr.io..."
  printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin
fi

echo "Pulling runtime images..."
compose pull nginx backend worker db

echo "Ensuring database is running before backup and migration..."
compose up -d db

echo "Creating pre-deploy backup..."
"$BACKUP_SCRIPT"

echo "Running Alembic migrations..."
compose run --rm backend alembic upgrade head

echo "Updating runtime services..."
compose up -d nginx backend worker

echo "Waiting for service health..."
compose up -d --wait nginx backend worker

echo "Verifying readiness endpoint through nginx..."
curl --fail --silent "http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready" >/dev/null

echo "Deploy complete."
