# Step 14 testing, resilience and performance gate evidence

Date: 2026-08-17

## Gate summary

The implementation-side Step 14 gate is green. The user approved the gate on
2026-08-17 before Step 15 packaging and deployment work began.

- 96 backend tests passed.
- Service/calculation line coverage is 98.52%, branch coverage is 94.55%, and
  Coverage.py's combined branch-aware display rounds to 98% (gate: at least
  80%).
- Critical calculation modules are 99-100% covered; settings validation is
  100% covered and the permission matrix has explicit success and denial tests.
- 22 frontend component tests passed.
- Ruff, MyPy, ESLint, Prettier, TypeScript, and the Vite production build passed.
- Six Playwright acceptance flows passed against the rebuilt live stack.
- Python and npm dependency audits found no known vulnerabilities.
- No critical or high defect remains open.

Machine-readable results are retained in:

- `step-14-backend-junit.xml`
- `step-14-backend-coverage.xml`
- `step-14-playwright-junit.xml`
- `step-14-playwright-artifacts/`

## Required failure and boundary cases

| Required case | Executed verification | Result |
|---|---|---|
| Database unavailable | `test_unavailable_database_returns_safe_readiness_error`; `/health` remains process-only while readiness returns a sanitized failure | Pass |
| API unavailable | Playwright aborts summary/latest requests, requires an explicit retryable error, and verifies that missing values are not replaced by zero | Pass |
| WebSocket interrupted | Playwright closes the live socket; component tests also cover heartbeat timeout, sequence gap, reconnect, and REST recovery | Pass |
| Stale device | Frozen-time demand/status tests exclude stale, disabled, and missing devices and report exclusions | Pass |
| Missing interval/sample | Completeness, empty-bucket, missing-baseline, missing-counter, peak, and cost fixtures preserve missing data without interpolation or fake zero | Pass |
| Duplicates | Database uniqueness, ingestion idempotency, and a live replay of 60 records all preserve one row per device/timestamp | Pass |
| Invalid authentication/authorization | Invalid login, invalid ingest key, unauthenticated reads, role denials, expiry, logout, and password/token log sanitization tests | Pass |

The live duplicate replay returned `accepted=0`, `duplicates=60`, `rejected=0`.
Its exact 60-row test timestamp range was deleted afterward and verified to
contain zero rows.

## Coverage

The final backend command collected 96 tests and reported:

| Module | Branch-aware coverage |
|---|---:|
| `app/services/audit.py` | 100% |
| `app/services/calculations.py` | 99% |
| `app/services/ingestion.py` | 100% |
| `app/services/live.py` | 93% |
| `app/services/readiness.py` | 90% |
| `app/services/settings.py` | 100% |
| **Total combined display** | **98%** |

The XML artifact reports an exact 98.52% line rate and 94.55% branch rate.

The permission suite explicitly covers viewer/operator/admin boundaries for
alarm acknowledgement, device writes, and settings writes. All critical
formula requirements have named tests in `test_calculations.py` for status,
current demand, cumulative energy/reset handling, completeness/gaps,
time-weighted demand, peak, comparison, aggregation, and Decimal cost.

## Performance and constrained-resource evidence

The API, web, and database containers were temporarily limited to one vCPU
each with memory limits of 512 MiB, 256 MiB, and 512 MiB respectively. This is
a stricter 1.25 GiB service envelope used as a documented Raspberry Pi-class
equivalent; it is not a claim of physical Pi testing. All original unlimited
container settings were restored by recreation and verified as
`NanoCpus=0`, `Memory=0`, and `MemorySwap=0` for all three services.

Authenticated API results under the constrained API limit (25 runs each):

| Operation | Median | p95 | Maximum | Target/result |
|---|---:|---:|---:|---|
| `/health` | 32.54 ms | 47.90 ms | 62.43 ms | Pass |
| `/ready` | 90.19 ms | 111.28 ms | 141.97 ms | Pass |
| Dashboard summary | 91.33 ms | 122.39 ms | 206.54 ms | Pass |
| Latest measurements | 51.38 ms | 91.71 ms | 93.66 ms | Pass |
| 24 h / 1 min history | 254.86 ms | 328.37 ms | 340.01 ms | Pass, below 2 s |

- A 60-record live ingestion batch completed in 556.58 ms at 107.8 records/s;
  all 60 records persisted and none was rejected.
- Ten loaded overview navigations reached the `Energy overview` heading at a
  median of 1068.67 ms and p95/maximum of 1301.33 ms, below the 2 s target.
- Chromium reported 68.01 MiB JavaScript heap after the navigation sample.
- A 15-second constrained run completed 209 authenticated summary requests.

Peak container observations during that request run:

| Container | Peak CPU | Peak memory share | Last observed memory |
|---|---:|---:|---:|
| API | 97.91% of one vCPU | 23.25% of 512 MiB | 107.6 MiB |
| Web | 0.27% of one vCPU | 43.17% of 256 MiB | 110.4 MiB |
| PostgreSQL | 31.95% of one vCPU | 14.33% of 512 MiB | 73.36 MiB |

## Clean-checkout rehearsal

A source-only copy was created on the requested C: drive at
`C:\CodexBuildCache\intelligent-energy-dashboard\step14-clean-checkout-20260817`.
No installed dependencies, build output, caches, or Git metadata were copied.
From that copy, the documented commands completed without source edits:

1. Created a fresh Python 3.12 virtual environment.
2. Installed both requirements files.
3. Ran `npm ci` (350 packages audited, zero vulnerabilities).
4. Created the isolated PostgreSQL database `energy_step14_clean`.
5. Upgraded Alembic from an empty database through revision `0003`.
6. Seeded all five fixed devices.
7. Passed Ruff, MyPy, 96 backend tests, 98.52% line coverage, and 94.55%
   branch coverage across the service/calculation target.
8. Passed 22 frontend tests, ESLint, Prettier, and a production build.
9. Validated the Compose configuration.
10. Removed only `energy_step14_clean` and verified that it no longer exists.

The C: source copy and its virtual environment remain available for review.

## Live deploy-artifact retest

Recreating the constrained containers exposed a stale API image that predated
the already-declared email validation dependency. The API image was rebuilt
from `requirements-backend.txt`, recreated, and retested. Final checks show:

- readiness `ready`, database `ready`, migration revision `0003`;
- administrator login succeeds;
- the login page returns HTTP 200;
- all six Playwright flows pass against the rebuilt image;
- persistent state remains 5 devices, 600 measurements, 7 settings, and the
  one retained Step 13 review alarm.

See `step-14-defects-retests.md` for the full defect history.

## Visual evidence

- `step-14-desktop-settings.png`: desktop authenticated settings workflow.
- `step-14-api-unavailable.png`: explicit API interruption and retry state.
- `step-14-mobile-devices.png`: loaded 375 px device workflow.

The screenshots were visually inspected after the final Playwright run.

## Known low-severity observations

- Vite reports a 743.07 kB main JavaScript chunk (220.00 kB gzip). This does
  not breach the measured page-load gate but should be code-split later.
- Starlette emits a test-client deprecation warning about the future `httpx2`
  migration. It does not affect current execution.

## Gate result

All mandatory Step 14 automated tests pass, coverage exceeds the threshold,
performance targets are met on the documented constrained equivalent, clean
setup is repeatable, and no critical/high defect is open. The user accepted
Step 14 on 2026-08-17.
