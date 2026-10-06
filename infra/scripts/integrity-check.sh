#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
env_file="${ENV_FILE:-${repo_root}/infra/.env.pi}"
compose_file="${repo_root}/infra/docker-compose.pi.yml"

compose=(docker compose --env-file "${env_file}" -f "${compose_file}")
database_result="$("${compose[@]}" exec -T db psql \
  --username=energy --dbname=energy --tuples-only --no-align --field-separator='|' \
  --set=ON_ERROR_STOP=1 --command="
    SELECT
      (SELECT version_num FROM alembic_version),
      (SELECT count(*) FROM devices),
      (SELECT count(*) FROM measurements),
      (SELECT count(*) FROM alarms),
      (SELECT count(*) FROM (
        SELECT device_id, measured_at
        FROM measurements
        GROUP BY device_id, measured_at
        HAVING count(*) > 1
      ) duplicate_groups);")"

IFS='|' read -r revision devices measurements alarms duplicate_groups <<< "${database_result}"
[[ "${duplicate_groups}" == "0" ]] || {
  printf 'Integrity check failed: %s duplicate measurement groups.\n' "${duplicate_groups}" >&2
  exit 1
}

lan_address="$(awk -F= '$1 == "LAN_BIND_ADDRESS" {sub(/^[^=]*=/, ""); gsub(/^[[:space:]\"'\'' ]+|[[:space:]\"'\'' ]+$/, ""); print; exit}' "${env_file}")"
dashboard_port="$(awk -F= '$1 == "DASHBOARD_PORT" {sub(/^[^=]*=/, ""); gsub(/[[:space:]]/, ""); print; exit}' "${env_file}")"
dashboard_port="${dashboard_port:-8080}"
base_url="${DASHBOARD_BASE_URL:-http://${lan_address}:${dashboard_port}}"

ready_payload="$(curl --fail --silent --show-error "${base_url}/ready")"
grep -q '"status":"ready"' <<< "${ready_payload}" || {
  printf 'Integrity check failed: readiness response was not ready.\n' >&2
  exit 1
}
curl --fail --silent --show-error "${base_url}/" | grep -qi '<!doctype html>' \
  || { printf 'Integrity check failed: dashboard HTML unavailable.\n' >&2; exit 1; }

printf 'revision=%s devices=%s measurements=%s alarms=%s duplicate_groups=%s ready=true\n' \
  "${revision}" "${devices}" "${measurements}" "${alarms}" "${duplicate_groups}"
