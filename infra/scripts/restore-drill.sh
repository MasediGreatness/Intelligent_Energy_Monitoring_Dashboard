#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
env_file="${ENV_FILE:-${repo_root}/infra/.env.pi}"
compose_file="${repo_root}/infra/docker-compose.pi.yml"
backup_path="${1:-}"
drill_project="${RESTORE_PROJECT_NAME:-intelligent-energy-restore-drill}"
drill_port="${RESTORE_DRILL_PORT:-18080}"

[[ -n "${backup_path}" && -f "${backup_path}" ]] \
  || { printf 'Usage: %s PATH_TO_BACKUP.dump\n' "$0" >&2; exit 1; }
[[ "${drill_project}" =~ ^[a-z0-9][a-z0-9_-]*restore-drill[a-z0-9_-]*$ ]] \
  || { printf 'RESTORE_PROJECT_NAME must contain restore-drill.\n' >&2; exit 1; }
[[ -f "${backup_path}.sha256" ]] \
  || { printf 'Missing checksum file %s.sha256\n' "${backup_path}" >&2; exit 1; }
(cd -- "$(dirname -- "${backup_path}")" && sha256sum --check "$(basename -- "${backup_path}.sha256")")

volume_name="${drill_project}_postgres_data"
if docker volume inspect "${volume_name}" >/dev/null 2>&1; then
  printf 'Refusing to reuse existing drill volume %s.\n' "${volume_name}" >&2
  exit 1
fi

compose=(docker compose --project-name "${drill_project}" \
  --env-file "${env_file}" -f "${compose_file}")
export LAN_BIND_ADDRESS=127.0.0.1
export DASHBOARD_PORT="${drill_port}"

"${compose[@]}" up --detach db
for _ in $(seq 1 60); do
  if "${compose[@]}" exec -T db pg_isready --username=energy --dbname=energy >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
"${compose[@]}" exec -T db pg_isready --username=energy --dbname=energy >/dev/null
"${compose[@]}" exec -T db pg_restore --username=energy --dbname=energy \
  --clean --if-exists --no-owner --no-privileges < "${backup_path}"
"${compose[@]}" run --rm migrate
"${compose[@]}" up --detach api web

for _ in $(seq 1 60); do
  if curl --fail --silent "http://127.0.0.1:${drill_port}/ready" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

ENV_FILE="${env_file}" DASHBOARD_BASE_URL="http://127.0.0.1:${drill_port}" \
  COMPOSE_PROJECT_NAME="${drill_project}" "${script_dir}/integrity-check.sh"
printf 'Restore drill is running at http://127.0.0.1:%s\n' "${drill_port}"
printf 'After visual review, remove only this drill with:\n'
printf 'docker compose --project-name %q --env-file %q -f %q down --volumes\n' \
  "${drill_project}" "${env_file}" "${compose_file}"
