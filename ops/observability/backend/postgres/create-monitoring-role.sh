#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT_DIR/../../.." && pwd)"
APP_STACK_DIR="$REPO_ROOT/ops/deployment/backend/app-stack"
TARGET_ENV="${APP_STACK_ENV:-${1:-prod}}"
APP_COMPOSE_FILE="$APP_STACK_DIR/compose.yml"
APP_COMPOSE_ENV="$APP_STACK_DIR/env/$TARGET_ENV/compose.env"
OBS_ENV="$ROOT_DIR/observability.env"
SQL_FILE="$ROOT_DIR/postgres/create-monitoring-role.sql"

for required_file in "$APP_COMPOSE_FILE" "$APP_COMPOSE_ENV" "$OBS_ENV" "$SQL_FILE"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Missing required file: $required_file" >&2
    exit 1
  fi
done

data_source_key="$(
  case "$TARGET_ENV" in
    prod)
      printf '%s' "PROD_DATA_SOURCE_NAME"
      ;;
    public)
      printf '%s' "PUBLIC_DATA_SOURCE_NAME"
      ;;
    *)
      echo "Unsupported environment: $TARGET_ENV" >&2
      echo "Expected one of: public, prod" >&2
      exit 1
      ;;
  esac
)"

monitor_password="$(
  python3 - "$OBS_ENV" "$data_source_key" <<'PY'
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

env_path = Path(sys.argv[1])
data_source_key = sys.argv[2]
data_source_name = None

for line in env_path.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    key, separator, value = stripped.partition("=")
    if separator and key == data_source_key:
        data_source_name = value.strip().strip('"').strip("'")
        break

if not data_source_name:
    raise SystemExit(f"{data_source_key} is missing from {env_path}")

parsed = urlparse(data_source_name)

if parsed.username != "lantern_monitor":
    raise SystemExit(f"{data_source_key} must use the lantern_monitor role before creating it")

if parsed.password is None:
    raise SystemExit(f"{data_source_key} must include the lantern_monitor password")

print(unquote(parsed.password), end="")
PY
)"

docker compose --env-file "$APP_COMPOSE_ENV" -f "$APP_COMPOSE_FILE" up -d db

docker compose --env-file "$APP_COMPOSE_ENV" -f "$APP_COMPOSE_FILE" exec -T \
  -e MONITOR_PASSWORD="$monitor_password" \
  db sh -lc 'psql -U "$POSTGRES_USER" "$POSTGRES_DB" -v monitor_password="$MONITOR_PASSWORD"' \
  < "$SQL_FILE"

echo "Ensured lantern_monitor role exists for $TARGET_ENV."
