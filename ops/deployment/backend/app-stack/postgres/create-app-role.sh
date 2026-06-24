#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/compose.yml"
COMPOSE_ENV="$ROOT_DIR/compose.env"
BACKEND_ENV="$ROOT_DIR/backend.env"
SQL_FILE="$ROOT_DIR/postgres/create-app-role.sql"

for required_file in "$COMPOSE_ENV" "$BACKEND_ENV" "$SQL_FILE"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Missing required file: $required_file" >&2
    exit 1
  fi
done

app_password="$(
  python3 - "$BACKEND_ENV" <<'PY'
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

env_path = Path(sys.argv[1])
database_url = None

for line in env_path.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    key, separator, value = stripped.partition("=")
    if separator and key == "DATABASE_URL":
        database_url = value.strip().strip('"').strip("'")
        break

if not database_url:
    raise SystemExit(f"DATABASE_URL is missing from {env_path}")

parsed = urlparse(database_url)

if parsed.username != "lantern_app":
    raise SystemExit("DATABASE_URL must use the lantern_app role before creating it")

if parsed.password is None:
    raise SystemExit("DATABASE_URL must include the lantern_app password")

print(unquote(parsed.password), end="")
PY
)"

docker compose --env-file "$COMPOSE_ENV" -f "$COMPOSE_FILE" up -d db

docker compose --env-file "$COMPOSE_ENV" -f "$COMPOSE_FILE" exec -T \
  -e APP_PASSWORD="$app_password" \
  db sh -lc 'psql -U "$POSTGRES_USER" "$POSTGRES_DB" -v app_password="$APP_PASSWORD"' \
  < "$SQL_FILE"

echo "Ensured lantern_app role exists."
