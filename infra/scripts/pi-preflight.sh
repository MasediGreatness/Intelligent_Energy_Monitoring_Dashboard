#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
env_file="${ENV_FILE:-${repo_root}/infra/.env.pi}"
compose_file="${repo_root}/infra/docker-compose.pi.yml"

fail() {
  printf 'Preflight failed: %s\n' "$1" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail "Docker is not installed."
docker info >/dev/null 2>&1 || fail "Docker Engine is not reachable."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is not available."
docker buildx version >/dev/null 2>&1 || fail "Docker Buildx/BuildKit is required."
[[ "${DOCKER_BUILDKIT:-1}" != "0" ]] \
  || fail "BuildKit is required; unset DOCKER_BUILDKIT=0."
[[ -f "${env_file}" ]] || fail "Create ${env_file} from infra/.env.pi.example."
grep -q 'CHANGE_ME' "${env_file}" && fail "Replace every CHANGE_ME placeholder."

machine_arch="$(uname -m)"
if [[ "${machine_arch}" != "aarch64" && "${machine_arch}" != "arm64" ]]; then
  [[ "${ALLOW_NON_ARM64:-0}" == "1" ]] || fail "Expected ARM64, found ${machine_arch}."
fi
[[ "$(getconf LONG_BIT)" == "64" ]] || fail "A 64-bit operating system is required."

lan_address="$(awk -F= '$1 == "LAN_BIND_ADDRESS" {sub(/^[^=]*=/, ""); gsub(/^[[:space:]\"'\'' ]+|[[:space:]\"'\'' ]+$/, ""); print; exit}' "${env_file}")"
[[ -n "${lan_address}" ]] || fail "LAN_BIND_ADDRESS is missing."
[[ "${lan_address}" != "0.0.0.0" ]] || fail "LAN_BIND_ADDRESS must not expose every interface."
case "${lan_address}" in
  10.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[01].*) ;;
  127.*)
    [[ "${ALLOW_LOOPBACK_BIND:-0}" == "1" ]] || fail "Loopback is for a local drill only."
    ;;
  *) fail "LAN_BIND_ADDRESS must be an RFC1918 private address." ;;
esac

if [[ "${lan_address}" != 127.* ]]; then
  ip -o -4 address show | grep -Fq " ${lan_address}/" \
    || fail "${lan_address} is not assigned to this host."
fi

mode="$(stat -c '%a' "${env_file}")"
if (( (8#${mode}) & 8#077 )); then
  fail "${env_file} must not be readable by group or other users; run chmod 600."
fi

available_kb="$(df -Pk "${repo_root}" | awk 'NR == 2 {print $4}')"
(( available_kb >= 4194304 )) || fail "At least 4 GiB free disk space is required."

docker compose --env-file "${env_file}" -f "${compose_file}" config --quiet
printf 'Preflight passed: arch=%s, bind=%s, env_mode=%s, free_kib=%s\n' \
  "${machine_arch}" "${lan_address}" "${mode}" "${available_kb}"
