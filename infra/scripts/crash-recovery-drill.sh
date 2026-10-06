#!/usr/bin/env bash
set -Eeuo pipefail

[[ "${1:-}" == "--confirm-abrupt-db-stop" ]] || {
  printf 'This sends SIGKILL to the selected Compose database.\n' >&2
  printf 'Rerun with --confirm-abrupt-db-stop after verifying ENV_FILE and COMPOSE_PROJECT_NAME.\n' >&2
  exit 2
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
env_file="${ENV_FILE:-${repo_root}/infra/.env.pi}"
compose_file="${repo_root}/infra/docker-compose.pi.yml"
compose=(docker compose --env-file "${env_file}" -f "${compose_file}")

before="$("${compose[@]}" exec -T db psql --username=energy --dbname=energy \
  --tuples-only --no-align --command='SELECT count(*) FROM measurements;')"
"${script_dir}/integrity-check.sh"

# Docker's init wrapper remains PID 1. Killing the postmaster child is an
# unexpected process loss; `docker kill` would be an operator stop and would
# intentionally suppress `unless-stopped` recovery.
"${compose[@]}" exec -T --user root db sh -c \
  'pid="$(head -n 1 "$PGDATA/postmaster.pid")"; test "$pid" -gt 1; kill -9 "$pid"' \
  || true
for _ in $(seq 1 90); do
  if "${compose[@]}" exec -T db pg_isready --username=energy --dbname=energy >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
"${compose[@]}" exec -T db pg_isready --username=energy --dbname=energy >/dev/null

for _ in $(seq 1 90); do
  if "${compose[@]}" exec -T api python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)" \
    >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

after="$("${compose[@]}" exec -T db psql --username=energy --dbname=energy \
  --tuples-only --no-align --command='SELECT count(*) FROM measurements;')"
"${script_dir}/integrity-check.sh"
[[ "${before}" == "${after}" ]] || {
  printf 'Unexpected measurement count change: before=%s after=%s\n' "${before}" "${after}" >&2
  exit 1
}
printf 'Abrupt database-stop recovery passed: measurements=%s before/after.\n' "${after}"
