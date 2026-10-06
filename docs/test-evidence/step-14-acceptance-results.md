# Step 14 requirements acceptance results

Date: 2026-08-17

This execution record complements `../acceptance-matrix.md`. `Pass` means the
implemented requirement has automated and/or reviewed evidence. `Deferred`
means its owning numbered step has not started; it is not counted as a Step 14
failure.

## Functional requirements

| Requirement | Status | Executed evidence |
|---|---|---|
| FR-001 | Pass | Step 11 Overview gate plus populated/error Playwright flow |
| FR-002 | Pass | Step 9 live gate and live client recovery tests |
| FR-003 | Pass | Step 12 History gate, URL/API regression, CSV fixture |
| FR-004 | Pass | Step 12 forecast/anomaly gate and unavailable-state test |
| FR-005 | Pass | Step 13 alarm lifecycle/API/UI/attribution checks |
| FR-006 | Pass | Step 13 device admin/disable/RBAC checks and mobile E2E |
| FR-007 | Pass | Step 13 settings checks plus exhaustive Step 14 validator tests |
| FR-008 | Pass | Deterministic simulator and all profile/scenario tests |
| FR-009 | Pass | One public ingestion contract used by simulator/gateway payloads |
| FR-010 | Pass | Ingestion authentication, validation, partial acceptance, and batch tests |
| FR-011 | Pass | Database uniqueness, API duplicate test, and 60-row live replay |
| FR-012 | Pass | Typed measurement schema/OpenAPI/data dictionary checks |
| FR-013 | Pass | Boundary, timestamp, quality, reset, and error fixtures |
| FR-014 | Pass | Frozen-time status boundary tests |
| FR-015 | Pass | Current-demand stale/disabled/missing exclusion tests |
| FR-016 | Pass | Counter baseline, reset, gap, and missing-counter tests |
| FR-017 | Pass | Time-weighted demand and incomplete-interval peak tests |
| FR-018 | Pass | Equal-elapsed-period comparison test |
| FR-019 | Pass | Decimal tariff/cost and missing-cost tests |
| FR-020 | Pass | Completeness/gap/empty-bucket tests |
| FR-021 | Pass | All six fixed aggregation intervals tested |
| FR-022 | Pass | Migration/schema/constraint/index integration gates |
| FR-023 | Pass | Argon2, login/logout/me, expiry, rate-limit, inactive-user tests |
| FR-024 | Pass | Viewer/operator/admin permission matrix and OpenAPI route inventory |
| FR-025 | Pass | Immutable audit and password/token log-sanitization tests |
| FR-026 | Pass | Process health, DB readiness, migration and DB-outage tests |
| FR-027 | Pass | Fixed read API inventory and integration suite |
| FR-028 | Pass | History/page/range boundary tests |
| FR-029 | Pass | Typed response/error/page contracts and generated client |
| FR-030 | Pass | Authenticated WebSocket envelope/protocol tests |
| FR-031 | Pass | Heartbeat, sequence-gap, reconnect, coalescing, and REST recovery tests |
| FR-032 | Pass | Loading/empty/error/stale/partial/missing component and E2E states |
| FR-033 | Pass | Seven-route E2E and loaded 375 px workflow |
| FR-034 | Pass | Step 10-13 visual/component reviews and final screenshots |
| FR-035 | Pass | Axe serious/critical smoke, semantic labels, keyboard/focus review |
| FR-036 | Pass | Typed configuration tests, placeholder-only example, secret/log checks |
| FR-037 | Pass | Empty-database upgrade through `0003` and database constraint gates |
| FR-038 | In progress | Step 15 owns ARM64 production packaging; Compose config passed at Step 14 |
| FR-039 | In progress | Step 15 owns operations runbook and drills |
| FR-040 | Deferred | Step 16 owns final demonstration rehearsal |
| FR-041 | In progress | Step 14 evidence is assembled; final handoff is owned by Step 16 |

## Non-functional requirements

| Requirement | Status | Executed evidence |
|---|---|---|
| NFR-001 | Pass | Approved architecture and thin route/service/repository boundaries |
| NFR-002 | Pass | WebSocket recovery always triggers authoritative REST refetch |
| NFR-003 | Pass | UTC/Johannesburg storage, API, calculation, and display tests |
| NFR-004 | Pass | Fixed SI names/types/precision across schema, API, and UI |
| NFR-005 | Pass | Missing-value and incomplete-series tests never fabricate zero |
| NFR-006 | Pass | History p95 328 ms, ingest 557 ms, loaded page p95 1.30 s |
| NFR-007 | Pass | Auth/RBAC/rate-limit/log tests; Python/npm audits report zero vulnerabilities |
| NFR-008 | Pass | Monitoring-only ADR and no control route/action in OpenAPI or UI |
| NFR-009 | Pass | DB/API/WS interruption and duplicate recovery cases pass |
| NFR-010 | Pass | Guarded isolated test DB plus clean-checkout database rehearsal |
| NFR-011 | Pass | All configured backend/frontend/static/E2E commands exit zero |
| NFR-012 | Pass | Service/calculation line 98.52%, branch 94.55%, with named formula/permission tests |
| NFR-013 | Pass | Structured request diagnostics and sanitized error/log tests |
| NFR-014 | Pass | C: clean source copy builds, migrates, seeds, tests, and validates Compose |
| NFR-015 | Pass | Central generated API client; formulas remain backend-owned |
| NFR-016 | Pass | Fixed decisions are captured in accepted ADR-001 through ADR-010 |
| NFR-017 | Pass | Desktop screenshots and loaded 375 px core workflow pass |
| NFR-018 | In progress | Physical Raspberry Pi/reboot/restore/power tests belong to Step 15 |
| NFR-019 | In progress | Current loopback bindings pass; final production exposure audit is Step 15 |
| NFR-020 | Deferred | Signed academic declaration and explanation review belong to Step 16 |

## Out-of-scope controls

OOS-001 through OOS-005 remain satisfied: the repository contains no firmware,
sensor electronics, ML training, executable industrial-load control, cloud
deployment, public-hosting configuration, or billing/production-certification
claim. The fixed monitoring-only boundary remains unchanged.
