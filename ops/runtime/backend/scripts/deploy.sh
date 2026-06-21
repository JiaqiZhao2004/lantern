#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/compose/compose.yml"
COMPOSE_ENV="$ROOT_DIR/compose/compose.env"
BACKEND_ENV="$ROOT_DIR/compose/backend.env"
DB_ENV="$ROOT_DIR/compose/db.env"

for required_file in "$COMPOSE_ENV" "$BACKEND_ENV" "$DB_ENV"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Missing required file: $required_file" >&2
    exit 1
  fi
done

compose() {
  docker compose --env-file "$COMPOSE_ENV" -f "$COMPOSE_FILE" "$@"
}

echo "Pulling runtime images..."
compose pull nginx backend worker db

echo "Ensuring database is running before backup and migration..."
compose up -d db

echo "Creating pre-deploy backup..."
"$ROOT_DIR/scripts/backup-db.sh"

echo "Running Alembic migrations..."
compose run --rm backend alembic upgrade head

echo "Updating runtime services..."
compose up -d nginx backend worker

echo "Waiting for service health..."
compose up -d --wait nginx backend worker

echo "Verifying readiness endpoint through nginx..."
curl --fail --silent "http://127.0.0.1:${NGINX_BIND_PORT:-8080}/health/ready" >/dev/null

echo "Deploy complete."
