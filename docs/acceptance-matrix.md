# Requirements Acceptance Matrix

Each requirement has a planned verification identifier. Detailed fixtures and executable tests are added in the numbered implementation step that owns the behaviour. `Review` means human inspection is essential; `Test` means automated where practical. The dated Step 14 execution status and evidence mapping is retained in [Step 14 acceptance results](test-evidence/step-14-acceptance-results.md).

## Functional requirements

| Requirement | Planned verification | Pass criterion |
|---|---|---|
| FR-001 | E2E-OVERVIEW-001 + CALC fixtures | Exact required panels render and values equal API/hand calculations. |
| FR-002 | E2E-LIVE-001 | Per-device fields and 60-minute trend update from test data. |
| FR-003 | E2E-HISTORY-001 + CSV-001 | Filters affect URL/API; charts and exported values match. |
| FR-004 | E2E-MLVIEW-001 | Forecast/confidence/model and complete anomaly semantics render; unavailable state is honest. |
| FR-005 | API-ALARM-001 + E2E-ALARM-001 | Lifecycle/filter/page/detail/authorised acknowledgement and audit pass. |
| FR-006 | API-DEVICE-001 + E2E-DEVICE-001 | Required metadata/status render; admin edits; disable preserves records. |
| FR-007 | API-SETTINGS-001 + E2E-SETTINGS-001 | Required settings read; valid admin edits persist/audit; invalid edits fail consistently. |
| FR-008 | SIM-DET-001 + SIM-SCENARIOS-001 | Five device types exist; same seed/range is identical; all scenarios are selectable. |
| FR-009 | CONTRACT-SOURCE-001 | Simulator and gateway-shaped payload use one schema; no simulator-only public field. |
| FR-010 | API-INGEST-001 | Valid, partial-invalid, malformed, oversized, and unauthorised cases return specified outcomes. |
| FR-011 | DB-DUP-001 + API-INGEST-DUP-001 | Constraint rejects second row; API reports duplicate without corruption. |
| FR-012 | CONTRACT-MEAS-001 | OpenAPI/schema snapshot contains exact field names, units, and meanings. |
| FR-013 | API-INGEST-VALIDATION-001 | Boundary, future-time, frequency-quality, enum, and reset fixtures behave exactly as specified. |
| FR-014 | CALC-STATUS-001 | Frozen-time fixtures classify online/stale/offline/disabled at boundaries. |
| FR-015 | CALC-DEMAND-001 | Hand fixture sum excludes stale/disabled/missing devices and reports exclusions. |
| FR-016 | CALC-ENERGY-001 | Midnight baseline, baseline gap, missing sample, and reset segment fixtures match by hand. |
| FR-017 | CALC-PEAK-001 | Time-weighted interval and daily maximum match controlled fixtures within tolerance. |
| FR-018 | CALC-COMPARE-001 | Equal elapsed windows are selected across local-day boundaries. |
| FR-019 | CALC-COST-001 | Decimal kWh × tariff equals labelled ZAR estimate without float drift. |
| FR-020 | CALC-COMPLETE-001 | Expected/valid counts, percent, and gaps match fixtures; no interpolation occurs. |
| FR-021 | API-AGG-001 | All six intervals return timestamp/count/completeness and correct controlled aggregates. |
| FR-022 | DB-SCHEMA-001 | Migration inspection/integration tests prove tables, fields, FKs, checks, uniqueness, and indexes. |
| FR-023 | API-AUTH-001 | Setup/login/logout/me, password hashing, expiry, rate limit, and inactive-user cases pass. |
| FR-024 | API-RBAC-001 | Permission matrix passes, including viewer/operator denials and absence of control endpoint. |
| FR-025 | API-AUDIT-001 + SECRET-LOG-001 | Required events are immutable and present; captured logs contain no password/token. |
| FR-026 | API-HEALTH-001 + API-READY-001 | Health survives DB outage; readiness safely distinguishes DB/migration failure. |
| FR-027 | API-INVENTORY-001 | OpenAPI includes every fixed method/route and integration success/error tests pass. |
| FR-028 | API-LIMITS-001 | Query/filter/page behaviour passes; >31-day, >24-hour raw, and >200 page requests fail safely. |
| FR-029 | CONTRACT-RESP-001 | Pagination/error/summary schemas and examples validate; no untyped route response. |
| FR-030 | WS-PROTOCOL-001 | Auth/subscription and every event type include envelope fields and monotonic sequence. |
| FR-031 | E2E-RECOVERY-001 | Heartbeat loss, backoff, sequence gap, reconnect, REST refetch, and event coalescing pass. |
| FR-032 | UI-STATES-001 | Visual/component tests cover loading/empty/error/stale/partial and missing displays `-`. |
| FR-033 | E2E-NAV-001 + VIEWPORT-001 | Seven routes/active nav pass at desktop/tablet/375 px; only tables intentionally scroll. |
| FR-034 | UI-TOKENS-001 + visual review | Tokens, status text/icons, precision, timestamps, charts, feedback, and reusable components comply. |
| FR-035 | A11Y-001 + manual keyboard review | No serious automated violation; all core actions have logical focus and labels. |
| FR-036 | CONFIG-001 + SECRET-SCAN-001 | Typed startup accepts valid/rejects missing config; no hard-coded URL/ID/credential/secret. |
| FR-037 | DB-MIGRATE-001 | Clean upgrade-to-head and one-revision downgrade pass; invalid enums/duplicates fail. |
| FR-038 | COMPOSE-001 + ARM64-001 | Clean Compose build starts required services; image manifests/builds support ARM64; policies are set. |
| FR-039 | OPS-DRILL-001 | A new reader completes setup/migrate/admin/seed/backup/restore/upgrade/rollback from docs. |
| FR-040 | DEMO-001 | Fresh seed reproduces all named scenarios and 7–10 minute flow. |
| FR-041 | HANDOFF-001 | Evidence checklist and traceability audit find no mandatory item missing. |

## Non-functional requirements

| Requirement | Planned verification | Pass criterion |
|---|---|---|
| NFR-001 | ARCH-BOUNDARY-001 review + static checks | UI uses API only; routes contain no SQL/formulas; service/repository boundaries are preserved. |
| NFR-002 | RECOVERY-AUTHORITY-001 | Restart/gap tests show REST restores committed state; WebSocket is not permanent storage. |
| NFR-003 | TIME-001 | DB/schema/API reject naive time; UTC serialization and Johannesburg display/boundaries pass. |
| NFR-004 | UNITS-001 | Schema/data dictionary/database/UI snapshots preserve names, types, and precision. |
| NFR-005 | MISSING-001 | Null/quality fixtures never become numeric/live zero. |
| NFR-006 | PERF-001 | LAN live latency ≤2 s; 24 h/1 m API ≤2 s on target/equivalent; 60-record target is measured and met. |
| NFR-007 | SECURITY-001 | Hash/session/role/rate-limit tests and repository/log secret scans pass. |
| NFR-008 | SAFETY-001 review + route/UI scan | No control route, event, command model, or enabled control button exists. |
| NFR-009 | FAILURE-001 | API/WS/DB interruption produces explicit UI state, recovery, no corrupt/duplicate row. |
| NFR-010 | TEST-ISOLATION-001 | Test startup refuses non-test database and leaves development data unchanged. |
| NFR-011 | QUALITY-001 | All configured lint, format-check, type, unit, component, and E2E commands exit 0. |
| NFR-012 | COVERAGE-001 | Service/calculation lines ≥80%; formula and permission requirement tests have complete mapping. |
| NFR-013 | LOGGING-001 | Logs are valid structured records with request IDs and sanitized central errors. |
| NFR-014 | CLEAN-CHECKOUT-001 | Documented clean-checkout setup/build/migrate/seed/test/run completes without source edits. |
| NFR-015 | TYPE-DRIFT-001 | Generated/central client matches OpenAPI; page components do not redefine response/calculation shapes. |
| NFR-016 | ADR-REVIEW-001 | Architecture/fixed-contract diffs have a prior approved ADR. |
| NFR-017 | VIEWPORT-001 | Desktop/tablet/375 px core workflows remain usable with no unintended overflow. |
| NFR-018 | PI-OPS-001 | Clean Pi install, reboot, restore, and power-interruption tests pass with recorded evidence. |
| NFR-019 | NETWORK-001 | Port/config scan proves LAN-only entry and no public DB/internal API exposure. |
| NFR-020 | OWNERSHIP-001 review | Signed/dated AI declaration and student explanation/reproduction review are complete. |

## Out-of-scope checks

| Item | Verification | Pass criterion |
|---|---|---|
| OOS-001 | Repository component/route scan | No firmware, sensor-electronics, calibration, or Modbus/RS-485 implementation. |
| OOS-002 | ML asset and UI review | No model training or invented results; fixed inputs are labelled simulated/future-service data. |
| OOS-003 | SAFETY-001 | No real or simulated executable industrial-load control path. |
| OOS-004 | Deployment review | No cloud/public-hosting configuration; LAN-only scope is explicit. |
| OOS-005 | Documentation review | No billing-grade or production-certification claim. |
