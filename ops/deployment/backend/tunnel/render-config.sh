#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$ROOT_DIR/config.yml.example"

hostname=""
production_hostname="lantern-api.royzhao.dev"
public_hostname="lantern-public-api.royzhao.dev"
tunnel_id=""
credentials_file=""
local_origin=""
production_local_origin="http://127.0.0.1:8080"
public_local_origin="http://127.0.0.1:8081"
output_path=""

usage() {
  cat <<'EOF'
Render a cloudflared config file from the checked-in template.

Usage:
  ./render-config.sh \
    --tunnel-id <tunnel-uuid> \
    --credentials-file /etc/cloudflared/<tunnel-uuid>.json \
    [--production-hostname lantern-api.royzhao.dev] \
    [--public-hostname lantern-public-api.royzhao.dev] \
    [--production-local-origin http://127.0.0.1:8080] \
    [--public-local-origin http://127.0.0.1:8081] \
    [--output /etc/cloudflared/config.yml]

If --output is omitted, the rendered config is written to stdout.

Compatibility:
  --hostname and --local-origin still work as aliases for the production
  hostname and production local origin.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hostname)
      hostname="${2:-}"
      shift 2
      ;;
    --production-hostname)
      production_hostname="${2:-}"
      shift 2
      ;;
    --public-hostname)
      public_hostname="${2:-}"
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
    --production-local-origin)
      production_local_origin="${2:-}"
      shift 2
      ;;
    --public-local-origin)
      public_local_origin="${2:-}"
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

if [[ -n "$hostname" ]]; then
  production_hostname="$hostname"
fi

if [[ -n "$local_origin" ]]; then
  production_local_origin="$local_origin"
fi

if [[ -z "$production_hostname" || -z "$public_hostname" || -z "$tunnel_id" || -z "$credentials_file" ]]; then
  echo "Missing required arguments." >&2
  usage >&2
  exit 1
fi

rendered_config="$(
  sed \
    -e "s|__PRODUCTION_HOSTNAME__|$production_hostname|g" \
    -e "s|__PUBLIC_HOSTNAME__|$public_hostname|g" \
    -e "s|__TUNNEL_ID__|$tunnel_id|g" \
    -e "s|__CREDENTIALS_FILE__|$credentials_file|g" \
    -e "s|__PRODUCTION_LOCAL_ORIGIN__|$production_local_origin|g" \
    -e "s|__PUBLIC_LOCAL_ORIGIN__|$public_local_origin|g" \
    "$TEMPLATE_PATH"
)"

if [[ -n "$output_path" ]]; then
  printf '%s\n' "$rendered_config" > "$output_path"
  echo "Wrote rendered config to $output_path"
else
  printf '%s\n' "$rendered_config"
fi
