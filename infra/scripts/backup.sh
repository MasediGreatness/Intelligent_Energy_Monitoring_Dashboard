#!/usr/bin/env bash
set -Eeuo pipefail

umask 077
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
env_file="${ENV_FILE:-${repo_root}/infra/.env.pi}"
compose_file="${repo_root}/infra/docker-compose.pi.yml"
backup_dir="${BACKUP_DIR:-${repo_root}/backups}"
timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
backup_path="${1:-${backup_dir}/energy-${timestamp}.dump}"

[[ -f "${env_file}" ]] || { printf 'Missing %s\n' "${env_file}" >&2; exit 1; }
mkdir -p -- "$(dirname -- "${backup_path}")"
[[ ! -e "${backup_path}" ]] || { printf 'Refusing to overwrite %s\n' "${backup_path}" >&2; exit 1; }

compose=(docker compose --env-file "${env_file}" -f "${compose_file}")
"${compose[@]}" exec -T db pg_dump \
  --username=energy --dbname=energy --format=custom \
  --no-owner --no-privileges > "${backup_path}"
pg_restore --list "${backup_path}" >/dev/null 2>&1 \
  || "${compose[@]}" exec -T db pg_restore --list < "${backup_path}" >/dev/null
sha256sum "${backup_path}" > "${backup_path}.sha256"
printf 'Backup verified: %s\nChecksum: %s.sha256\n' "${backup_path}" "${backup_path}"
