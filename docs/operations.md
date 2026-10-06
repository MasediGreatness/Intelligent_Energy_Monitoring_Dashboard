# Raspberry Pi 4 deployment and recovery runbook

Date: 2026-08-17

## Scope and safety boundary

This runbook deploys the monitoring-only dashboard on a 64-bit Raspberry Pi 4
and exposes only its Nginx entry point on one explicitly selected private LAN
address. PostgreSQL and FastAPI have no host port in the production Compose
file. Nothing here enables relay, contactor, load-shedding, restoration, or any
other industrial control action.

The commands below are run from the repository root on the Pi. Replace example
addresses and usernames with the deployment's real values. Never commit
`infra/.env.pi`, backups, private keys, or passwords.

## 1. Prerequisites and initial setup

Use 64-bit Raspberry Pi OS on an ARM64 Pi 4 with at least 4 GiB free disk, a
stable private IPv4 address, accurate time, Docker Engine, the Docker Compose
v2 plugin, Docker Buildx/BuildKit, `curl`, and `sha256sum`. Add the deployment
user to the `docker` group only if that level of host privilege is understood
and accepted. Unset `DOCKER_BUILDKIT=0` if it exists; the multi-platform
Dockerfiles require BuildKit.

```bash
cp infra/.env.pi.example infra/.env.pi
chmod 600 infra/.env.pi
chmod +x infra/scripts/*.sh
openssl rand -hex 24  # DB_PASSWORD: 48 hexadecimal characters
openssl rand -hex 32  # APP_SECRET_KEY: 64 hexadecimal characters
openssl rand -hex 32  # INGEST_API_KEY: 64 hexadecimal characters
```

Put the generated values into `infra/.env.pi`. Set `LAN_BIND_ADDRESS` to the
Pi's exact RFC1918 address, not `0.0.0.0`, and keep
`TARGET_PLATFORM=linux/arm64`. The hexadecimal database password is deliberate:
it remains safe when Compose constructs the fixed `DATABASE_URL`.

```bash
./infra/scripts/pi-preflight.sh
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml build --pull
```

Preflight rejects placeholders, non-ARM64/32-bit hosts, insecure env-file
permissions, non-private/wildcard addresses, addresses not assigned to the
host, insufficient disk, and invalid Compose configuration.

## 2. Database, migrations, administrator and first start

Start the database, apply the single Alembic head, and create the administrator
explicitly. The password is read without echo and removed from the shell
environment immediately after use.

```bash
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml up -d db
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml run --rm migrate

read -rsp 'Administrator password: ' ENERGY_SETUP_PASSWORD; echo
export ENERGY_SETUP_PASSWORD
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml run --rm \
  -e ENERGY_SETUP_PASSWORD api python -m app.cli.create_user \
  --email admin@intelligentenergy.com --role admin
unset ENERGY_SETUP_PASSWORD

docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml up -d api web
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml ps
curl --fail "http://PI_PRIVATE_IP:8080/health"
curl --fail "http://PI_PRIVATE_IP:8080/ready"
```

For a clearly labelled demonstration dataset only, temporarily set
`SIMULATOR_ENABLED=true` in `infra/.env.pi`, run the seed command, then restore
the intended deployment setting and recreate the API:

```bash
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml run --rm \
  api python -m app.simulator.cli seed
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml up -d --force-recreate api
```

The dashboard is `http://PI_PRIVATE_IP:8080/`. Configure the host firewall to
allow that TCP port only from the intended private subnet. Do not forward this
port from an internet router. The database and API remain reachable only on
the internal Docker network.

## 3. Reboot verification

All long-running services use `restart: unless-stopped`. After a planned Pi
reboot, verify both container and application health:

```bash
sudo reboot
# Reconnect after the host returns.
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml ps
./infra/scripts/integrity-check.sh
```

The pass condition is healthy database/API/web services, readiness at the
single migration head, dashboard HTML available, and zero duplicate
`(device_id, measured_at)` groups.

## 4. Backup

The backup script creates a PostgreSQL custom-format dump with mode 600,
validates its catalog, and writes a SHA-256 checksum. Copy both files to a
separate protected device; a backup stored only on the Pi is not recovery.

```bash
./infra/scripts/backup.sh
# Or choose an explicit new path; existing files are never overwritten.
./infra/scripts/backup.sh backups/before-upgrade.dump
```

Record the application image tag, Alembic revision, backup filename, checksum,
UTC time, and operator in the maintenance log. Test restoration regularly.

## 5. Restore into a clean volume

Never prove a backup by overwriting the live volume. The drill script requires
a verified dump/checksum, rejects an existing drill volume, restores into the
separate `intelligent-energy-restore-drill_postgres_data` volume, applies any
forward migrations, starts the dashboard on loopback port 18080, and runs the
integrity check.

```bash
RESTORE_DRILL_PORT=18080 ./infra/scripts/restore-drill.sh \
  backups/energy-YYYYMMDDTHHMMSSZ.dump
```

Open `http://127.0.0.1:18080`, sign in with the restored administrator, and
compare device, measurement, alarm, and setting records with the source. After
recording evidence, remove only the drill project and its clean test volume:

```bash
docker compose --project-name intelligent-energy-restore-drill \
  --env-file infra/.env.pi -f infra/docker-compose.pi.yml down --volumes
```

The production project and its named volume are not addressed by this command.

## 6. Upgrade

Use immutable release tags. Do not upgrade from an uncommitted working tree.

```bash
./infra/scripts/backup.sh backups/before-upgrade.dump
git fetch --tags
git checkout VERIFIED_RELEASE_TAG
# Set IMAGE_TAG to the same immutable release identifier in infra/.env.pi.
./infra/scripts/pi-preflight.sh
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml build --pull
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml run --rm migrate
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml up -d api web
./infra/scripts/integrity-check.sh
```

Inspect the migration and release notes before applying them. Keep the prior
images and verified backup until the new version completes functional review.

## 7. Rollback

If the schema is still backward compatible, set `IMAGE_TAG` back to the prior
verified tag and recreate API/web with `--no-build`. Never improvise an Alembic
downgrade on live data.

```bash
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml up -d \
  --no-build --force-recreate api web
./infra/scripts/integrity-check.sh
```

If the release changed data incompatibly, stop API/web and restore the
pre-upgrade dump into a new clean project/volume using the documented restore
drill. Review it, then schedule an explicit volume cutover. Retain the old
volume until the user accepts the restored system. This recovery-first rule is
safer than destructive in-place schema reversal.

## 8. Abrupt-stop and physical power-interruption testing

The guarded crash script sends SIGKILL only after the explicit confirmation
flag. Run it first against the separate restore-drill project, never as the
first experiment on the only production copy:

```bash
COMPOSE_PROJECT_NAME=intelligent-energy-restore-drill \
ENV_FILE=infra/.env.pi DASHBOARD_BASE_URL=http://127.0.0.1:18080 \
  ./infra/scripts/crash-recovery-drill.sh --confirm-abrupt-db-stop
```

The script requires PostgreSQL/API recovery, unchanged measurement count, a
readable dashboard, current migration head, and zero duplicate groups.

The Step 15 gate still requires a real Pi power-interruption review:

1. Take and verify a backup on separate media.
2. Run `integrity-check.sh` and record counts.
3. With the simulator or gateway ingesting fixed timestamped records, remove
   Pi power without a shutdown once, then restore power.
4. Wait for restart policies and health checks, rerun `integrity-check.sh`, and
   make a fresh verified backup.
5. Confirm the dashboard renders the retained records and duplicate groups are
   zero. An in-flight PostgreSQL transaction may be wholly present or wholly
   absent; a retried identical timestamp may be reported as a duplicate, but
   no partial/corrupt row or second unique row is acceptable.
6. Record Pi model/OS, UTC start/end, before/after counts, service health,
   screenshots, observations, operator, and signature under
   `docs/test-evidence`.

## 9. Routine checks and shutdown

```bash
./infra/scripts/integrity-check.sh
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml logs \
  --since 24h api web db
docker compose --env-file infra/.env.pi -f infra/docker-compose.pi.yml stop
```

Compose bounds each service's JSON logs to three 10 MiB files. Use `stop` for a
planned application shutdown and `sudo poweroff` before removing normal power.
