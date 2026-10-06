# Step 16 defects and retests

Date: 2026-10-05

| ID | Severity | Observation | Correction | Retest |
|---|---|---|---|---|
| D16-001 | Medium | Adding the demo script broke the Step 15 packaging test's exact operational-script inventory. | Added `prepare-demo.sh` to the expected inventory and asserted its refusal guard and abnormal-scenario coverage. | Targeted packaging suite: 5/5 passed. |
| D16-002 | High | The first rehearsal generated each scenario from its catalog base counter, producing ten artificial cumulative-energy decreases between adjacent scenario windows. | Demo staging now offsets every later scenario onto the last stored counter while retaining generated increments and measurements. No reset is invented. | Fresh-volume rerun: zero counter decreases before and after power-quality staging; duplicate groups zero. |
| D16-003 | Medium | Initial power-quality staging attempted to construct a dictionary directly from a SQLAlchemy chunked result and raised `TypeError`. | Replaced the constructor with explicit `(code, device_id)` iteration. | Power-quality mode inserted five rows and reported `LOAD-002` PF 0.7204/0.7208 in independent isolated runs. |
| D16-004 | Low | An immediately staged dropout could overlap recent fixture timestamps and be silently deduplicated. | Added a timestamp guard that reports the required wait and exits before writing. | Early run refused with a wait interval; waited isolated retest inserted 540 rows and retained zero duplicate groups. |
| D16-005 | High | Current dependency audits found vulnerable development-only Pytest and JavaScript transitive versions. | Raised the Pytest floor to the fixed 9.0.3 line and refreshed the npm lockfile to fixed Vitest/Redocly/brace-expansion/js-yaml/source-map-js versions. | Full backend/frontend suites pass on the updated dependencies; `pip-audit`, production `npm audit`, and full `npm audit` report zero known vulnerabilities. |
| D16-006 | High | Gateway mode forced `Secure` cookies while the supplied Pi Nginx profile is HTTP-only, preventing LAN browser login. | Added explicit `SESSION_COOKIE_SECURE`, defaulted it false for private-LAN HTTP, documented true only behind tested TLS, and forwarded it through Compose. | Configuration and login-header tests cover both modes; local HTTP production login transport is usable without weakening a future HTTPS profile. |
| D16-007 | Medium | The fixed security contract required both login and ingestion rate limits, but ingestion had only key authentication and a batch bound. | Added a per-client 120 requests/minute ingestion limiter and the standard 429 error envelope. | The integration test accepts the first 120 requests and rejects request 121 with `RATE_LIMIT_EXCEEDED`. |
| D16-008 | Low | The demo manifest's single maximum could be the anomaly window rather than the scripted peak window, and SQLAlchemy 2.1 exposed deprecated tuple-result calls. | Reported overall and scripted-peak maxima separately and removed deprecated `.tuples()` calls. | Final clean-volume manifest reports 33.894 kW overall, 31.848 kW scripted peak, 30.331 kW limit, and no SQLAlchemy tuple deprecation. |

No critical/high Step 16 defect remains open in the preparation tooling. Human
browser timing, acknowledgement, explanation/signature and physical Pi checks
remain gate actions rather than software defects.
