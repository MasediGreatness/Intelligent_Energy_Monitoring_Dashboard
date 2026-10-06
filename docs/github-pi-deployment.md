# GitHub-to-Raspberry-Pi deployment

This guide publishes the tested API and web containers to GitHub Container
Registry (GHCR), then pulls them onto a 64-bit Raspberry Pi 4. The Pi remains
the application host: GitHub stores source and container images but does not
run PostgreSQL or the FastAPI backend.

The production safety boundary is unchanged. Only Nginx is bound to the Pi's
selected private LAN address. FastAPI and PostgreSQL have no host ports and
remain on the internal Docker network. The dashboard is monitoring-only.

## 1. Protect the GitHub account and repository

Never put a GitHub password, personal access token, application secret,
database password, backup, or `infra/.env.pi` in this repository. GitHub does
not use an account password for Git command-line authentication. Use browser or
SSH authentication for Git, and a narrowly scoped token only where GHCR
requires it. If any credential has been pasted into a chat, issue, terminal
history, or other untrusted location, rotate it before continuing and enable
two-factor authentication.

The canonical repository is
[`MasediGreatness/Intelligent_Energy_Monitoring_Dashboard`](https://github.com/MasediGreatness/Intelligent_Energy_Monitoring_Dashboard).
It is currently public. Changing that visibility is a governance decision:
keep it public only when public source distribution is intentional, and never
commit secrets or operational data. On the development computer, authenticate
with GitHub CLI or configure an SSH key, then publish the existing repository:

```bash
gh auth login --web --git-protocol ssh
git branch -M main
git remote add origin git@github.com:MasediGreatness/Intelligent_Energy_Monitoring_Dashboard.git
git add .
git commit -m "Initial intelligent energy dashboard release"
git push -u origin main
```

The repository owner is the GitHub account name `MasediGreatness`, not an email
address. Before the first commit, inspect
`git status` and confirm that `infra/.env.pi`, `.env` files, `backups/`, keys,
database files, and generated test data are absent.

Recommended repository settings are:

- require the workflow checks before merging to the default branch;
- require two-factor authentication for repository collaborators;
- leave Actions workflow permissions at read-only by default;
- allow this repository's workflow to create packages;
- choose GHCR package visibility deliberately and keep it consistent with the
  source-distribution decision.

No repository secret is required to publish images. The workflow uses the
short-lived, repository-scoped `GITHUB_TOKEN`; only its publish job receives
`packages: write`, while every other job is read-only.

## 2. What the workflow publishes

`.github/workflows/container-release.yml` runs backend migrations/tests and
quality checks, frontend tests/lint/build, and real Buildx builds for both
`linux/amd64` and `linux/arm64`. Only after those jobs pass does it publish:

```text
ghcr.io/<lowercase-owner>/<lowercase-repository>-api
ghcr.io/<lowercase-owner>/<lowercase-repository>-web
```

Both images receive matching tags:

- `sha-<short-commit>` for every successful default-branch publication;
- `latest` for the current successful default-branch build;
- `vX.Y.Z` when a matching Git tag is pushed.

Each published image also includes build provenance and an SBOM. Pull requests
build both architectures but cannot publish packages.

For a release, merge a fully reviewed commit, then create and push a version
tag. Use a new tag for every release; never move an existing release tag.

```bash
git switch main
git pull --ff-only
git tag -a v1.0.1 -m "Intelligent Energy Dashboard v1.0.1"
git push origin v1.0.1
```

Open the repository's **Actions** page and wait for `Test and publish container
images` to pass. The two packages will then appear under the repository or
account Packages view. A `sha-...` tag is suitable for a commit-pinned test;
the version tag is clearer for an approved deployment. Avoid deploying
`latest` because it changes after later default-branch builds.

## 3. Prepare a 64-bit Raspberry Pi 4

Use a 64-bit Raspberry Pi OS installation, stable storage, accurate time, and a
reserved private IPv4 address. Install Git, OpenSSL, curl, Docker Engine,
Buildx, and Docker Compose v2 from Docker's official Debian repository. Verify
the result:

```bash
uname -m
getconf LONG_BIT
docker version
docker compose version
docker buildx version
```

`uname -m` must report `aarch64` or `arm64`, and `getconf LONG_BIT` must report
`64`. If the deployment user is added to the `docker` group, treat that account
as root-equivalent and sign out and back in before continuing.

### Give the Pi read-only source access

For the current public repository, clone over HTTPS without a credential:

```bash
git clone https://github.com/MasediGreatness/Intelligent_Energy_Monitoring_Dashboard.git
cd Intelligent_Energy_Monitoring_Dashboard
```

If the repository is later made private, create a dedicated SSH deploy key on
the Pi instead:

```bash
install -d -m 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -f "$HOME/.ssh/intelligent_energy_deploy" \
  -C "intelligent-energy-pi" -N ""
cat "$HOME/.ssh/intelligent_energy_deploy.pub"
```

In GitHub, open **Repository settings → Deploy keys → Add deploy key**, paste
the public key, and leave write access disabled. Then clone the repository and
make future pulls use only that key:

```bash
GIT_SSH_COMMAND="ssh -i $HOME/.ssh/intelligent_energy_deploy -o IdentitiesOnly=yes" \
  git clone git@github.com:MasediGreatness/Intelligent_Energy_Monitoring_Dashboard.git
cd Intelligent_Energy_Monitoring_Dashboard
git config core.sshCommand \
  "ssh -i $HOME/.ssh/intelligent_energy_deploy -o IdentitiesOnly=yes"
```

### Give the Pi read-only package access

Private GHCR packages require a read-only package credential. Create a personal
access token (classic) with only `read:packages`; authorize SSO if the account's
organization requires it. Prefer a dedicated machine account that has read
access to only this repository and its packages. Do not grant package
write/delete scopes or store the token in the repository.

```bash
read -rsp 'GHCR read token: ' GHCR_READ_TOKEN; echo
printf '%s' "$GHCR_READ_TOKEN" | \
  docker login ghcr.io --username MasediGreatness --password-stdin
unset GHCR_READ_TOKEN
chmod 600 "$HOME/.docker/config.json"
```

For public packages, the login is unnecessary. Docker's standard config stores
the login credential for later pulls, so protect the Pi account and its home
directory.

## 4. Create the Pi-only runtime configuration

From the repository root on the Pi:

```bash
cp infra/.env.pi.example infra/.env.pi
chmod 600 infra/.env.pi
chmod +x infra/scripts/*.sh
openssl rand -hex 24
openssl rand -hex 32
openssl rand -hex 32
nano infra/.env.pi
```

Put the three generated values into `DB_PASSWORD`, `APP_SECRET_KEY`, and
`INGEST_API_KEY`, respectively. Set the exact private address assigned to the
Pi and configure the two GHCR image names. A release configuration resembles:

```dotenv
COMPOSE_PROJECT_NAME=intelligent-energy-dashboard
TARGET_PLATFORM=linux/arm64
API_IMAGE=ghcr.io/masedigreatness/intelligent_energy_monitoring_dashboard-api
WEB_IMAGE=ghcr.io/masedigreatness/intelligent_energy_monitoring_dashboard-web
IMAGE_TAG=v1.0.1
LAN_BIND_ADDRESS=192.168.1.50
DASHBOARD_PORT=8080
```

Keep all other values from the example, keep `SIMULATOR_ENABLED=false` for a
real gateway deployment, and keep `SESSION_COOKIE_SECURE=false` while using the
documented private-LAN HTTP URL. Set it to `true` only after adding and testing
HTTPS/TLS termination; otherwise browsers will not send the login cookie over
HTTP. Do not quote or reuse secrets. Owner, repository, and image names must be
lowercase. `infra/.env.pi` is ignored by Git and must remain Pi-local with mode
`600`.

The GHCR overlay removes all Compose `build` definitions. Render both files
together and verify that every service has an image and no service has a build:

```bash
docker compose --env-file infra/.env.pi \
  -f infra/docker-compose.pi.yml -f infra/docker-compose.ghcr.yml \
  --profile tools config --quiet
```

The base preflight performs the ARM64, disk, permissions, private-IP, and
production configuration checks:

```bash
./infra/scripts/pi-preflight.sh
```

## 5. Pull and start the approved release

Use the base production file and the pull-only overlay for every command:

```bash
compose=(docker compose --env-file infra/.env.pi \
  -f infra/docker-compose.pi.yml -f infra/docker-compose.ghcr.yml)

"${compose[@]}" pull db api web
"${compose[@]}" up -d --no-build db
"${compose[@]}" run --rm migrate
```

Create the initial administrator. The password is entered without echo and is
never written to an environment file:

```bash
read -rsp 'Administrator password: ' ENERGY_SETUP_PASSWORD; echo
export ENERGY_SETUP_PASSWORD
"${compose[@]}" run --rm -e ENERGY_SETUP_PASSWORD api \
  python -m app.cli.create_user \
  --email admin@intelligentenergy.com --role admin
unset ENERGY_SETUP_PASSWORD
```

Start the application, inspect the resolved port boundary, and run the
integrity check:

```bash
"${compose[@]}" up -d --no-build api web
"${compose[@]}" ps
test -z "$("${compose[@]}" port api 8000)"
test -z "$("${compose[@]}" port db 5432)"
"${compose[@]}" port web 80
curl --fail "http://PI_PRIVATE_IP:8080/health"
curl --fail "http://PI_PRIVATE_IP:8080/ready"
./infra/scripts/integrity-check.sh
```

The two `docker port` checks for API and database must produce no mappings.
Only the web service should publish port 80 to the exact configured private
address and dashboard port. Open `http://PI_PRIVATE_IP:8080/` from a machine on
the permitted LAN. Do not configure internet router port forwarding.

`restart: unless-stopped` brings the three long-running services back after a
normal Pi reboot. Complete the clean-install, reboot, clean-volume restore, and
physical power-interruption checks in
`docs/test-evidence/step-15-pi-hardware-checklist.md` before accepting the Pi as
production-ready.

## 6. Upgrade without rebuilding on the Pi

First verify that the target workflow passed and read its migration/release
notes. From the Pi repository, preserve the local `infra/.env.pi`, take a
verified off-device backup, and fetch the approved source tag:

```bash
./infra/scripts/backup.sh backups/before-upgrade.dump
git fetch --tags --prune
git checkout v1.1.0
nano infra/.env.pi  # set IMAGE_TAG=v1.1.0

compose=(docker compose --env-file infra/.env.pi \
  -f infra/docker-compose.pi.yml -f infra/docker-compose.ghcr.yml)
"${compose[@]}" pull api web
"${compose[@]}" run --rm migrate
"${compose[@]}" up -d --no-build --force-recreate api web
./infra/scripts/integrity-check.sh
```

Keep the previous image tag, source tag, database volume, and verified backup
until the new release passes review. Do not enable an unattended updater:
database migrations and operational checks require an intentional release.

## 7. Roll back application images

If the release notes confirm that the current schema is backward-compatible,
restore the previous `IMAGE_TAG`, pull it, and recreate only API and web:

```bash
nano infra/.env.pi
compose=(docker compose --env-file infra/.env.pi \
  -f infra/docker-compose.pi.yml -f infra/docker-compose.ghcr.yml)
"${compose[@]}" pull api web
"${compose[@]}" up -d --no-build --force-recreate api web
./infra/scripts/integrity-check.sh
```

If a migration is not backward-compatible, do not improvise an in-place
Alembic downgrade. Follow the clean-volume restore and reviewed cutover process
in `docs/operations.md`.

## Troubleshooting

- `denied` while pulling: confirm `docker login ghcr.io`, package visibility,
  account access to the repository, `read:packages`, and required SSO approval.
- `no matching manifest for linux/arm64`: confirm the Actions workflow's
  multi-platform publish job passed and inspect it with
  `docker buildx imagetools inspect IMAGE:TAG`.
- `exec format error`: confirm 64-bit Raspberry Pi OS and
  `TARGET_PLATFORM=linux/arm64`.
- Compose tries to build: include both `-f` arguments in the documented order
  and confirm `docker compose ... --profile tools config` contains no `build`.
- Port bind failure: make sure `LAN_BIND_ADDRESS` is currently assigned to the
  Pi and the selected port is unused.
- Dashboard unhealthy: inspect bounded logs with
  `"${compose[@]}" logs --since 30m db api web`, then verify `/ready` before
  changing data or recreating the database volume.

For backup, restore, crash-recovery, shutdown, and physical test procedures,
use `docs/operations.md`; this guide only replaces local image builds with
verified GHCR pulls.
