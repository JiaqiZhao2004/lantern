#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/observability.env"
OUTPUT_DIR="$ROOT_DIR/generated"
OUTPUT_FILE="$OUTPUT_DIR/alertmanager.yml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing required file: $ENV_FILE" >&2
  echo "Copy observability.env.example to observability.env and fill in SMTP settings." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required_vars=(
  SMTP_SMARTHOST
  SMTP_FROM
  SMTP_USERNAME
  SMTP_PASSWORD
  SMTP_REQUIRE_TLS
  ALERT_EMAIL_TO
)

for required_var in "${required_vars[@]}"; do
  if [[ -z "${!required_var:-}" ]]; then
    echo "Set $required_var in $ENV_FILE." >&2
    exit 1
  fi
done

mkdir -p "$OUTPUT_DIR"
umask 077

python3 - "$OUTPUT_FILE" <<'PY'
import os
import sys
from pathlib import Path

output_file = Path(sys.argv[1])

def sq(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

content = f"""global:
  smtp_smarthost: {sq(os.environ["SMTP_SMARTHOST"])}
  smtp_from: {sq(os.environ["SMTP_FROM"])}
  smtp_auth_username: {sq(os.environ["SMTP_USERNAME"])}
  smtp_auth_password: {sq(os.environ["SMTP_PASSWORD"])}
  smtp_require_tls: {os.environ["SMTP_REQUIRE_TLS"].lower()}

route:
  receiver: email
  group_by: ["alertname", "severity"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

receivers:
  - name: email
    email_configs:
      - to: {sq(os.environ["ALERT_EMAIL_TO"])}
        send_resolved: true
"""

tmp_file = output_file.with_suffix(".tmp")
tmp_file.write_text(content, encoding="utf-8")
tmp_file.replace(output_file)
PY

echo "Rendered $OUTPUT_FILE"
