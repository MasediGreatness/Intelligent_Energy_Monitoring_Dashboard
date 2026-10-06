# Intelligent Industrial Energy Dashboard

Monitoring and advisory dashboard subsystem for the postgraduate project
**Intelligent Industrial Energy Monitoring and Predictive Load Management
System**. It accepts deterministic simulator data today and preserves the same
ingestion boundary for a future Raspberry Pi gateway.

## Project status

- Steps 1-14: implemented, tested, and accepted.
- Step 15 implementation and local recovery rehearsal: passed.
- Step 15 physical Raspberry Pi gate: **not yet verified**. A clean Pi install,
  reboot, clean-volume restore, and real power-interruption test remain required.
- Step 16 handoff: documentation and demonstration assets are prepared for
  student review; the explanation and AI-use declarations remain unsigned until
  the student personally verifies them.

This repository must not be described as Raspberry Pi validated until the
[physical Pi checklist](docs/test-evidence/step-15-pi-hardware-checklist.md) is
completed and signed.

## Safety boundary

This MVP is read-only monitoring and advisory software. It contains no enabled
path for starting, stopping, shedding, restoring, or otherwise controlling a
relay, contactor, or industrial load. Forecasts, anomalies, and simulator
outputs are informational. Real control requires a separate hardware, safety,
authority, hazard-analysis, and verification specification. See
[ADR-003](docs/decisions/ADR-003-monitoring-only-safety-boundary.md).

## What is implemented

- Responsive authenticated pages for Overview, Live Monitoring, Energy
  History, Forecast and Anomalies, Alarms, Devices, and Settings.
- Validated, idempotent measurement ingestion plus deterministic normal, peak,
  low-power-factor, overconsumption, dropout, and meter-reset scenarios.
- Backend-authoritative current demand, energy, equal-period comparison,
  time-weighted demand, daily peak, completeness, and estimated-cost rules.
- PostgreSQL persistence with Alembic migrations, audit history, explicit roles,
  opaque sessions, bounded queries, and generated OpenAPI/TypeScript contracts.
- Sequenced WebSocket notifications with heartbeat, reconnect, gap detection,
  and authoritative REST recovery.
- ARM64-compatible production images, Nginx, health checks, bounded logs,
  restart policies, a named database volume, and guarded backup/recovery tools.

## Architecture and fixed stack

```text
simulator now / authenticated Pi gateway later
                    |
                    v
        FastAPI validation and services
                    |
                    v
       PostgreSQL + Alembic migrations
                    |
             REST (authority)
          WebSocket (notification)
                    |
                    v
          React/TypeScript dashboard
```

- Backend: Python 3.12, FastAPI, Pydantic
- Database: PostgreSQL 17, SQLAlchemy 2, Alembic, Psycopg 3
- Frontend: React, TypeScript, Vite, TanStack Query, Recharts, Tailwind CSS
- Deployment: Docker Compose and Nginx, targeting Raspberry Pi 4 ARM64
- Verification: Pytest/HTTPX, Ruff, mypy, Vitest, React Testing Library, and
  Playwright

Read the [architecture](docs/architecture.md), [data dictionary](docs/data-dictionary.md),
[API contract](docs/api-contract.md), and [decision index](docs/decisions/README.md)
before changing a field, unit, route, formula, role, or safety boundary.

## Repository layout

```text
apps/api/       FastAPI app, SQLAlchemy models, Alembic migrations, tests
apps/web/       React dashboard, generated API types, component and E2E tests
infra/          Development/Pi Compose, Nginx, and guarded operations scripts
docs/           Architecture, contracts, decisions, evidence, demo, limitations
Documentation/  Controlling project documents supplied by the student
```

## Quick start with Docker Desktop

Prerequisites are Git and Docker Desktop with Docker Compose. Python 3.12 and
Node.js 24 are needed only when running checks directly on the host.

1. Copy the example configuration and replace **every** `CHANGE_ME` value with
   a unique random value. Never commit `.env`.

   ```powershell
   Copy-Item .env.example .env
   # Generate each secret independently, then paste it into .env.
   $bytes = [byte[]]::new(32)
   [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
   [Convert]::ToHexString($bytes).ToLowerInvariant()
   ```

2. Build and start the local stack, then apply all migrations.

   ```powershell
   docker compose --env-file .env -f infra/docker-compose.yml up --build -d
   docker compose --env-file .env -f infra/docker-compose.yml exec api `
     alembic -c alembic.ini upgrade head
   docker compose --env-file .env -f infra/docker-compose.yml exec api `
     alembic -c alembic.ini current
   ```

3. Seed the five stable device records and create an administrator explicitly.
   No default user or password is created by migrations or startup.

   ```powershell
   docker compose --env-file .env -f infra/docker-compose.yml exec api `
     python -m app.simulator.cli seed

   $adminPassword = Read-Host -AsSecureString
   $env:ENERGY_SETUP_PASSWORD = `
     [System.Net.NetworkCredential]::new('', $adminPassword).Password
   docker compose --env-file .env -f infra/docker-compose.yml exec `
     -e ENERGY_SETUP_PASSWORD="$env:ENERGY_SETUP_PASSWORD" api `
     python -m app.cli.create_user `
       --email admin@intelligentenergy.com --role admin
   Remove-Item Env:ENERGY_SETUP_PASSWORD
   ```

   The password must be unique and at least 12 characters. The command stores
   an Argon2 hash and never prints the password.

4. Generate reproducible demonstration data and open the dashboard.

   ```powershell
   docker compose --env-file .env -f infra/docker-compose.yml exec api `
     python -m app.simulator.cli generate `
       --start 2026-08-15T10:00:00Z --seconds 600 `
       --scenario normal --persist
   ```

   Open <http://localhost:5173/login>. Process health is
   <http://localhost:8000/health>; database/migration readiness is
   <http://localhost:8000/ready>; development OpenAPI documentation is
   <http://localhost:8000/docs>.

5. Stop the stack without deleting its named volumes.

   ```powershell
   docker compose --env-file .env -f infra/docker-compose.yml down
   ```

See [simulator scenarios](docs/simulator.md) for every scenario and
[the demonstration script](docs/demo.md) for the repeatable 7-10 minute path.

## Host development environment

Create the checked-in dependency environment from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install `
  -r requirements-backend.txt -r requirements-dev.txt
Set-Location apps/web
npm ci
Set-Location ../..
```

Run the complete host checks:

```powershell
Set-Location apps/api
..\..\.venv\Scripts\pytest.exe -q --cov=app.services --cov-branch `
  --cov-report=term-missing
..\..\.venv\Scripts\ruff.exe check app alembic tests
..\..\.venv\Scripts\mypy.exe app

Set-Location ../web
npm run generate:api
npm test
npm run lint
npm run build
```

`apps/api/openapi.json` is the committed API source used to generate
`apps/web/src/api/generated.ts`; generated types must not be edited by hand.
Playwright setup and evidence commands are recorded in the
[Step 15 gate record](docs/test-evidence/step-15-packaging-operations-gate.md).

## Raspberry Pi 4 and GitHub deployment

- For an on-device source build and all operational safeguards, follow the
  [Raspberry Pi runbook](docs/operations.md).
- For GitHub Actions-built ARM64 images in GitHub Container Registry, follow
  [GitHub-to-Pi deployment](docs/github-pi-deployment.md).
- Do not expose PostgreSQL or FastAPI host ports. The production Compose file
  publishes only Nginx on one explicitly configured private LAN address.
- Complete the [physical Pi checklist](docs/test-evidence/step-15-pi-hardware-checklist.md)
  before claiming deployment acceptance.

## Engineering handoff records

- [Requirements](docs/requirements.md)
- [Final requirements traceability](docs/final-requirements-traceability.md)
- [Final test summary](docs/test-summary.md)
- [Acceptance matrix](docs/acceptance-matrix.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Data dictionary and calculation meanings](docs/data-dictionary.md)
- [REST/WebSocket API contract](docs/api-contract.md)
- [Architecture decision index](docs/decisions/README.md)
- [Known limitations and remaining integrations](docs/limitations.md)
- [Demonstration guide](docs/demo.md)
- [Raspberry Pi deployment and recovery runbook](docs/operations.md)
- [Step 15 implementation evidence](docs/test-evidence/step-15-packaging-operations-gate.md)
- [AI Use Declaration template](docs/ai-use-declaration.md)

## Academic ownership

The student must personally review, understand, execute, and be able to explain
every design choice, calculation, test, and limitation. The AI declaration in
this repository is deliberately unsigned: only the student can describe the
actual assistance used, record personal verification, and sign/date the final
submission declaration.
