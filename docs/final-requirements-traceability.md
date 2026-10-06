# Final requirements traceability

Date prepared: 2026-10-05

## Status rules

- **Pass** means implementation and retained automated/review evidence satisfy
  the requirement within the development environment.
- **Ready for reviewer** means the implementation and procedure exist, but the
  required student/reviewer execution or signature is not yet recorded.
- **Pending physical Pi** means local or cross-build evidence exists but cannot
  substitute for the specified Raspberry Pi 4 check.

This record does not convert pending hardware or academic-ownership checks into
passes. Detailed executed results remain in `docs/test-evidence`; planned test
identifiers remain in [acceptance-matrix.md](acceptance-matrix.md).

## Functional requirements

| ID | Design / implementation source | Verification evidence | Final status |
|---|---|---|---|
| FR-001 | Overview page; dashboard-summary service/API | Step 11 gate; Step 14 six-flow E2E | Pass |
| FR-002 | Live page; latest/history APIs; live client | Step 9 and Step 11 gates | Pass |
| FR-003 | History page; backend aggregation; CSV builder | Step 12 gate and CSV fixture | Pass |
| FR-004 | Forecast/anomaly page and fixed schemas | Step 12 gate; deterministic anomaly fixture | Pass |
| FR-005 | Alarm read/acknowledge routes and Alarms page | Step 13 API/UI/RBAC/audit tests | Pass |
| FR-006 | Device model/read/write routes and Devices page | Step 13 create/edit/disable and mobile E2E | Pass |
| FR-007 | Settings service/routes/page | Step 13 gate; Step 14 exhaustive validators | Pass |
| FR-008 | Simulator catalog, generator, scenarios and CLI | Simulator unit/determinism/scenario tests; Step 5/14 evidence | Pass |
| FR-009 | Public measurement schema shared by simulator/gateway | Ingestion contract tests and OpenAPI snapshot | Pass |
| FR-010 | Authenticated bounded partial-accept ingestion service | Ingestion integration suite | Pass |
| FR-011 | Measurement unique constraint and conflict handling | DB duplicate and ingestion replay tests | Pass |
| FR-012 | Measurement schemas, data dictionary and OpenAPI | Contract/schema tests; generated client | Pass |
| FR-013 | Pydantic plus service/database validation | Boundary, timestamp, frequency, reset and quality tests | Pass |
| FR-014 | `device_status` calculation and status APIs | Frozen-time boundary tests | Pass |
| FR-015 | `current_demand` service and summary endpoint | Hand-calculated exclusion fixtures | Pass |
| FR-016 | `energy_from_counter` service | Baseline, gap, null and reset fixtures | Pass |
| FR-017 | Time-weighted interval and qualified peak calculations | Controlled interval/peak fixtures | Pass |
| FR-018 | Equal-period comparison service | Local-day equal-window fixture | Pass |
| FR-019 | Decimal estimated-cost service and labels | Decimal/no-float-drift tests | Pass |
| FR-020 | Completeness/gap calculation and response fields | Missing/empty/gap fixtures | Pass |
| FR-021 | Fixed raw/10s/1m/15m/1h/1d aggregation | Calculation and API aggregation tests | Pass |
| FR-022 | SQLAlchemy domain model and Alembic `0001`-`0003` | Clean migration/schema/index/constraint gate | Pass |
| FR-023 | Login/logout/me, session model and setup CLI | Step 8 auth/hash/expiry/rate-limit tests | Pass |
| FR-024 | Viewer/operator/admin dependencies and monitoring-only routes | Step 8/13 permission matrix; OpenAPI scan | Pass |
| FR-025 | Audit service and immutable system events | Step 8/13 event and sanitized-log tests | Pass |
| FR-026 | `/health`, `/ready` and migration-head checks | DB-outage/readiness tests; Step 14 failure flow | Pass |
| FR-027 | Versioned API router inventory | Step 7 integration suite; validated OpenAPI | Pass |
| FR-028 | Typed query/page/range limits | History/page/range boundary tests | Pass |
| FR-029 | Typed response models, page and error envelope | Contract tests, examples and generated client | Pass |
| FR-030 | Authenticated WebSocket hub/protocol | Step 9 protocol/coalescing integration tests | Pass |
| FR-031 | Heartbeat, gap detection, backoff and REST recovery | Live-client unit tests; Step 14 interruption E2E | Pass |
| FR-032 | Shared loading/empty/error/stale/partial components | Component tests and failure E2E | Pass |
| FR-033 | App shell, seven routes and responsive navigation | Step 10 route/accessibility review; Step 14 mobile E2E | Pass |
| FR-034 | CSS tokens, status semantics, formats and reusable UI | Step 10-13 visual reviews; Step 14 screenshots | Pass |
| FR-035 | Semantic controls, focus, contrast and reduced motion | Axe smoke plus keyboard/viewport review | Pass |
| FR-036 | Typed settings and placeholder-only environment examples | Configuration tests and secret scan | Pass |
| FR-037 | Alembic lifecycle and DB constraints | Clean upgrade/downgrade and invalid enum/duplicate tests | Pass |
| FR-038 | ARM64 multi-stage images and production Compose | Step 15 ARM builds, render, health/restart/log/volume tests | Pass |
| FR-039 | Operations runbook and guarded maintenance scripts | Step 15 local restore/recovery; Pi/new-reader execution outstanding | Ready for reviewer |
| FR-040 | [demo.md](demo.md) and non-destructive staged simulator script | Script contract/syntax and isolated fresh-seed rehearsal; assessed 7-10 minute run outstanding | Ready for reviewer |
| FR-041 | Architecture/data/API/ADR/evidence/traceability/handoff documents | Step 14/15 artifacts plus Step 16 audit; signature and Pi evidence outstanding | Ready for reviewer |

## Non-functional requirements

| ID | Design / implementation source | Verification evidence | Final status |
|---|---|---|---|
| NFR-001 | UI -> versioned API -> services -> repositories -> PostgreSQL | Architecture review and route/repository inspection | Pass |
| NFR-002 | PostgreSQL/REST authority; WebSocket notification only | Sequence-gap/restart tests and recovery E2E | Pass |
| NFR-003 | UTC database/API plus Johannesburg presentation | Timestamp validation and local-day calculation tests | Pass |
| NFR-004 | Unit-bearing schema names and numeric mappings | Schema/data/API/UI contract inspection | Pass |
| NFR-005 | Null plus data quality, never fabricated zero | Calculation/component/error-flow tests | Pass |
| NFR-006 | Bounded API/history/live performance | Step 14 response/ingest/page table; physical Pi repeat pending under NFR-018 | Pass on documented equivalent |
| NFR-007 | Argon2, HttpOnly sessions, role enforcement and rate limits | Step 8/14 security suite and dependency/secret audits | Pass |
| NFR-008 | Monitoring-only ADR and absent control surface | Route/OpenAPI/UI scan | Pass |
| NFR-009 | Visible interruption and idempotent recovery | Step 14 failure tests; Step 15 crash/restore rehearsal | Pass locally |
| NFR-010 | Guarded isolated test database | Test startup checks and clean-copy rehearsal | Pass |
| NFR-011 | Ruff/MyPy/Pytest and ESLint/Prettier/Vitest/Playwright gates | Step 16 final regression: 105 backend, 22 frontend and 6 browser tests passed | Pass |
| NFR-012 | Service/calculation branch-aware coverage | Step 16: 98.82% line, 94.55% branch | Pass |
| NFR-013 | Structured request logs and central sanitized errors | Middleware/error/log tests | Pass |
| NFR-014 | Clean checkout build/migrate/seed/test/run instructions | Step 14 clean C: rehearsal; operations and demo guides | Pass locally |
| NFR-015 | OpenAPI-generated/central TypeScript client; backend formulas | Contract generation and architecture review | Pass |
| NFR-016 | ADR-001 through final accepted fixed decisions | ADR review history and no silent contract change | Pass |
| NFR-017 | Desktop/tablet/375 px behavior | Step 10 manual review; Step 14/15 screenshots/E2E | Pass |
| NFR-018 | Production Compose and Pi operations checklist | ARM64/local restore/crash pass; clean Pi, reboot, restore and physical power-loss record absent | Pending physical Pi |
| NFR-019 | Exact LAN bind; DB/API on internal network | Compose contract/runtime port scan; repeat on target Pi checklist | Pass locally |
| NFR-020 | AI declaration and personal explanation/signature | Declaration template and [explanation sign-off](test-evidence/step-16-explanation-signoff.md) | Ready for reviewer |

## Out-of-scope controls

| ID | Evidence | Status |
|---|---|---|
| OOS-001 | Repository has no firmware, sensing electronics, calibration, or Modbus/RS-485 driver implementation. | Preserved |
| OOS-002 | Simulator labels fixed forecast/anomaly contract data; repository has no model training pipeline or predictive-accuracy claim. | Preserved |
| OOS-003 | ADR-003, OpenAPI and UI contain no executable industrial-load control path. | Preserved |
| OOS-004 | Production deployment is private-LAN Compose; no public-cloud exposure is claimed. | Preserved |
| OOS-005 | Documentation makes no billing-grade or production-certification claim. | Preserved |

## Demonstration trace audit

The reproducible fixture chain is:

1. Stable UUIDv5 device catalog and seed `118` select deterministic inputs.
2. Scenario generation produces unit-bearing measurement records, forecasts,
   and one explained anomaly.
3. PostgreSQL uniqueness preserves one row per device/timestamp.
4. Backend calculation services derive dashboard metrics; React displays API
   values and does not recalculate engineering formulas.
5. The demo alarm fixtures are calculated from stored combined peak demand and
   the stored demand limit, then clearly identified by source
   `deterministic_demo_fixture`.
6. Acknowledgement records the authenticated actor/time/note and an immutable
   event.
7. WebSocket recovery causes a REST refetch from authoritative stored state.

The field-by-field rule table and presenter actions are in [demo.md](demo.md).
The remaining review record is in
[step-16-demonstration-gate.md](test-evidence/step-16-demonstration-gate.md).

## Remaining integration work

### Raspberry Pi gateway

- Build the separate calibrated sensing/gateway subsystem and submit batches
  through `POST /api/v1/ingest/measurements` with `X-Ingest-Key`.
- Define device provisioning, key rotation, buffering/retry, clock sync,
  calibration traceability, network-loss behavior, and hardware acceptance.
- Reuse the current measurement contract; do not add simulator-only fields or
  let the gateway write directly to PostgreSQL.

### Forecasting and anomaly ML

- Train and validate models outside this dashboard repository with versioned
  datasets, leakage controls, accuracy/error metrics, drift monitoring, and an
  explicit deployment rollback.
- Publish only the existing forecast/anomaly contracts, including model version,
  bounds, expected/actual values, score, explanation, and provenance.
- Replace fixture labels only after real model evidence exists; never present a
  missing prediction as zero or silently mix simulated and model output.

### Alarm evaluation

- Implement a continuous backend rule evaluator if operational automatic alarms
  are required. It must own hysteresis, deduplication, clear conditions, and
  audit provenance and must be covered by an approved ADR and tests.
- Until then, the Step 16 demand alarms remain explicitly labelled deterministic
  demonstration fixtures.

### Load control

- Real start/stop/shed/restore control remains prohibited and out of scope.
- Any future control subsystem requires a separate safety case, hazard analysis,
  fail-safe hardware, interlocks, authentication/authorization design, manual
  override, commissioning plan, regulatory review, and a new approved contract.
  It must not be enabled by repurposing this monitoring API or UI.

## Items blocking final sign-off

1. Complete and sign the physical Raspberry Pi checklist: clean install,
   reboot, clean-volume restore, and one controlled physical power interruption.
2. Execute the 7-10 minute demonstration from a fresh demo volume, retain the
   prepare/final manifests, and record defects/retests.
3. Have the student explain and sign each design/formula/test/limitation item in
   the Step 16 explanation checklist without relying on generated prose.
4. Sign and date the institution-compatible AI Use Declaration after personally
   verifying its statements.

Until those records exist, the engineering package is implementation-complete
but not finally accepted.
