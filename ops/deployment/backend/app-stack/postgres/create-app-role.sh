#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ENV="${APP_STACK_ENV:-${1:-prod}}"
if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [public|prod|<env-name>]" >&2
  exit 1
fi

ENV_DIR="$ROOT_DIR/env/$TARGET_ENV"
COMPOSE_FILE="$ROOT_DIR/compose.yml"
COMPOSE_ENV="$ENV_DIR/compose.env"
BACKEND_ENV="$ENV_DIR/backend.env"
DB_ENV="$ENV_DIR/db.env"
SQL_FILE="$ROOT_DIR/postgres/create-app-role.sql"

if [[ ! -d "$ENV_DIR" ]]; then
  echo "Missing environment directory: $ENV_DIR" >&2
  exit 1
fi

for required_file in "$COMPOSE_ENV" "$BACKEND_ENV" "$DB_ENV" "$SQL_FILE"; do
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
    actual_user = parsed.username or "<missing>"
    raise SystemExit(
        "DATABASE_URL in backend.env must use the lantern_app runtime role "
        f"before this helper can create it; found user {actual_user!r}. "
        "Keep the bootstrap postgres credentials in db.env, and set "
        "DATABASE_URL=postgresql+psycopg://lantern_app:<app-password>@lantern-[prod|public]-db:5432/lantern "
        "in backend.env."
    )

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
