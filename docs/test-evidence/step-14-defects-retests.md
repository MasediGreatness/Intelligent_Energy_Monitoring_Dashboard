# Step 14 defect and retest log

Date: 2026-08-17

| ID | Initial severity | Observation | Resolution | Retest/result | State |
|---|---|---|---|---|---|
| D14-001 | Medium | Playwright could not start because its Chromium binary was not installed in the fresh frontend runtime. | Installed the Playwright-managed Chromium runtime using the documented command. | Six E2E flows passed, including the final run against the rebuilt live API. | Closed |
| D14-002 | Medium | A new missing-counter fixture initially expected a one-kWh delta, which contradicted the fixed cumulative-counter rule. | Corrected the fixture to preserve the valid counter segment (three kWh) and removed an unreachable defensive branch after typed filtering. | 96 backend tests passed; calculations reached 99% in the combined branch-aware report. | Closed |
| D14-003 | Medium | Vitest collected the Playwright E2E file and failed before running it. | Added an explicit `e2e/**` exclusion to the Vitest configuration while retaining the directory in the TypeScript build. | 22 component tests, lint, formatting, build, and six Playwright tests passed. | Closed |
| D14-004 | Low | The first 375 px evidence screenshot was captured while device data was still loading. | Waited for `LOAD-001` before screenshot capture. | The final mobile screenshot contains the loaded five-device table and usable navigation/actions. | Closed |
| D14-005 | High | Recreating the constrained containers reused a stale API image that lacked `email-validator`; API startup became unhealthy. | Rebuilt the API image from the current declared runtime requirements and recreated API/web with the existing runtime secrets and persistent database volume. | Readiness is green at `0003`, login succeeds, web returns 200, all six E2E flows pass, data counts are intact, and all temporary limits are restored. | Closed |

## Open observations

| ID | Severity | Observation | Disposition |
|---|---|---|---|
| O14-001 | Low | Vite warns that the main production chunk exceeds 500 kB. | Retain as optimization debt; measured loaded overview p95 is 1.30 s under the constrained test. |
| O14-002 | Low | Starlette's current test client emits a future `httpx2` deprecation warning. | Track during dependency maintenance; all 96 tests pass with the supported current stack. |

No critical or high defect remains open.
