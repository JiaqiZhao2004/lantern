#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$ROOT_DIR/config.yml.example"

hostname=""
tunnel_id=""
credentials_file=""
local_origin="http://127.0.0.1:8080"
output_path=""

usage() {
  cat <<'EOF'
Render a cloudflared config file from the checked-in template.

Usage:
  ./render-config.sh \
    --hostname lantern-api.royzhao.dev \
    --tunnel-id <tunnel-uuid> \
    --credentials-file /etc/cloudflared/<tunnel-uuid>.json \
    [--local-origin http://127.0.0.1:8080] \
    [--output /etc/cloudflared/config.yml]

If --output is omitted, the rendered config is written to stdout.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hostname)
      hostname="${2:-}"
      shift 2
      ;;
    --tunnel-id)
      tunnel_id="${2:-}"
      shift 2
      ;;
    --credentials-file)
      credentials_file="${2:-}"
      shift 2
      ;;
    --local-origin)
      local_origin="${2:-}"
      shift 2
      ;;
    --output)
      output_path="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$hostname" || -z "$tunnel_id" || -z "$credentials_file" ]]; then
  echo "Missing required arguments." >&2
  usage >&2
  exit 1
fi

rendered_config="$(
  sed \
    -e "s|__BACKEND_PUBLIC_HOSTNAME__|$hostname|g" \
    -e "s|__TUNNEL_ID__|$tunnel_id|g" \
    -e "s|__CREDENTIALS_FILE__|$credentials_file|g" \
    -e "s|__LOCAL_ORIGIN__|$local_origin|g" \
    "$TEMPLATE_PATH"
)"

if [[ -n "$output_path" ]]; then
  printf '%s\n' "$rendered_config" > "$output_path"
  echo "Wrote rendered config to $output_path"
else
  printf '%s\n' "$rendered_config"
fi
