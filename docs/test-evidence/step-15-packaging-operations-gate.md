# Step 15 packaging and operations gate evidence

Date: 2026-08-18

## Gate summary

The implementation-side Step 15 work is ready for review. The overall gate is
not yet accepted because the build plan requires a clean install, reboot,
backup restore, and physical power-interruption test on a real Raspberry Pi 4
ARM64. Those checks cannot be represented by local Docker emulation. The
reviewer checklist is `step-15-pi-hardware-checklist.md`.

No Step 16 work has started.

## Production packaging

- `apps/api/Dockerfile` is a multi-stage Python 3.12 image. The runtime copies
  only the virtual environment, application, migrations, and Alembic config;
  it runs as non-root `10001:10001` and has a process health check.
- `apps/web/Dockerfile` builds React/Vite separately and serves only `dist`
  from Nginx. Its architecture-independent build runs on BuildKit's native
  build platform, while the final image uses the requested target platform.
- The four production bases—Python 3.12 slim Bookworm, Node 24 Alpine, Nginx
  1.29 Alpine, and PostgreSQL 17 Alpine—publish `linux/arm64/v8` manifests.
- Actual no-export `linux/arm64` builds completed for both final targets. Build
  records `pyu0st9q5nfcaka57v4ing4b0` (API, 10m20s) and
  `e75cqjmgbya98d3ebpatw619m` (web, 1m47s) are retained in local BuildKit
  history.
- Final native rehearsal images are
  `intelligent-energy-dashboard-api:step15` at
  `sha256:7d33eb2bc3fc5b788b8a03888e1132fdf299f65abf19def809cbcd017f4736e4`
  and `intelligent-energy-dashboard-web:step15` at
  `sha256:68801cbf751ac7d3e82d4f212a56a84b336c288a1a0b8fe4a08764b6aebff3f0`.

The rendered production Compose model contains `db`, `migrate`, `api`, and
`web`; only web has a host binding. The local drill rendered that exact bind
as `127.0.0.1:18082:80`. API showed only container port 8000 and PostgreSQL
only container port 5432. The backend network rendered as internal. Database,
API, and web each have a health check, `unless-stopped`, init, bounded
`json-file` logs (`10m`, three files), and `no-new-privileges`. PostgreSQL uses
the named `postgres_data` volume.

## Runbook and guarded tools

`docs/operations.md` covers Pi prerequisites and preflight, secret setup,
migrations, explicit administrator creation, optional demonstration seeding,
LAN/firewall rules, reboot verification, backup, clean-volume restore,
upgrade, rollback, abrupt-stop recovery, physical power interruption, routine
checks, and shutdown.

The following guarded scripts were added and all pass Bash syntax validation:

- `pi-preflight.sh`
- `backup.sh`
- `integrity-check.sh`
- `restore-drill.sh`
- `crash-recovery-drill.sh`

The backup script refuses overwrite, emits a PostgreSQL custom-format dump,
validates its catalog, and writes a SHA-256 file. The restore script refuses an
existing drill volume. The crash script requires an explicit confirmation flag
and kills the PostgreSQL child behind the init wrapper so Docker treats it as
an unexpected process failure rather than an operator stop.

## Backup, clean-volume restore, and recovery rehearsal

An isolated source project and a separate, previously absent restore-drill
volume were exercised with native production images. The source backup was:

```text
C:\CodexBuildCache\intelligent-energy-dashboard\step15\step15-source-with-records.dump
SHA-256 c1fdf369d3b7e666f0f4f06d732c04e80078acf22b948c4cb8aedd34d5e0e24b
```

Its catalog validates with PostgreSQL 17 `pg_restore --list`. After restoring
into the clean volume, source and restored records matched exactly:

| Dataset | Revision | Devices | Measurements | Forecasts | Users | Settings | Duplicate groups |
|---|---:|---:|---:|---:|---:|---:|---:|
| Source | 0003 | 5 | 600 | 5 | 2 | 7 | 0 |
| Clean restore | 0003 | 5 | 600 | 5 | 2 | 7 | 0 |

Both `/ready` responses reported database ready, migrations at head `0003`,
and both dashboards returned HTTP 200.

The restored PostgreSQL postmaster child was then sent SIGKILL. Docker recorded
one restart, PostgreSQL returned healthy, API readiness returned to `0003`, and
all counts above remained unchanged with zero duplicate groups. A second
validated backup was created after the crash:

```text
C:\CodexBuildCache\intelligent-energy-dashboard\step15\step15-post-crash.dump
SHA-256 bebca7dc2e8e2fae24a9da55889621799028b2adf3c34816ce48a9d9dd925d2f
```

Docker Desktop was later restarted after the ARM cross-build. Both isolated
projects returned automatically under their restart policies, their databases
remained healthy, and the exact record/duplicate counts above still matched.
This is useful host-restart evidence, but it is not claimed as a Pi reboot or a
physical power-loss result.

After evidence capture, only the two labelled isolated rehearsal projects and
their test volumes were removed. The verified C: backups, test artifacts,
production image tags, and normal development stack were retained.

## Automated and visual verification

- Ruff and strict MyPy: pass.
- Backend: 102/102 tests pass.
- Service/calculation coverage: 333/338 lines (98.52%) and 104/110 branches
  (94.55%); combined display 98%.
- Frontend: 22/22 component tests pass; ESLint, Prettier, TypeScript, and Vite
  production build pass.
- Final production source stack: 6/6 Playwright flows pass in 30.93 seconds.
- Clean restored stack: 6/6 Playwright flows pass in 30.47 seconds.
- Production Compose render, packaging contract tests, Bash syntax checks,
  native builds, and actual ARM64 target builds pass.

Machine-readable results and visually inspected screenshots are retained as:

- `step-15-backend-junit.xml`
- `step-15-backend-coverage.xml`
- `step-15-playwright-junit.xml`
- `step-15-restore-playwright-junit.xml`
- `step-15-desktop-settings.png`
- `step-15-api-unavailable.png`
- `step-15-mobile-devices.png`
- `step-15-restore-desktop-settings.png`
- `step-15-restore-api-unavailable.png`
- `step-15-restore-mobile-devices.png`

The final E2E run used a random password and a disposable administrator. Its
five sessions, five audit rows, and user row were removed in one scoped test
cleanup; no alarm or setting referenced that fixture. The retained source and
restore counts therefore still match.

## Known observations

- Vite still reports the accepted low-severity 743.07 kB main bundle warning
  (220.00 kB gzip).
- Starlette's test-client warning about a future `httpx2` migration remains
  low-severity dependency-maintenance work.
- The production Nginx image starts its master as the image default user and
  drops workers according to the official image config. Compose additionally
  applies a read-only filesystem and `no-new-privileges`.

## Gate result

Implementation and local recovery evidence: **Pass**.

Physical Raspberry Pi Step 15 gate: **Pending user test and review**. Complete
all three sections of `step-15-pi-hardware-checklist.md`, attach the requested
outputs/screenshots, and approve Step 15 only if the clean install/reboot,
clean-volume restore, and real power-interruption checks all pass.
