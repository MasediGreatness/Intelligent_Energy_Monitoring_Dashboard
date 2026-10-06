# Final test summary

Final automated execution date: 2026-10-06 (Africa/Johannesburg)

## Release gates

| Gate | Final result | Retained evidence |
|---|---|---|
| Backend tests | 105 passed; 0 failed/skipped | `test-evidence/step-16-backend-junit.xml` |
| Backend service coverage | 334/338 lines (98.82%); 104/110 branches (94.55%) | `test-evidence/step-16-backend-coverage.xml` |
| Python quality | Ruff passed; strict MyPy passed on 52 source files | Final Step 16 execution log / CI workflow |
| Frontend component tests | 22 passed in 3 files | Final Step 16 execution log / CI workflow |
| Frontend quality/build | ESLint and Prettier passed; TypeScript/Vite production build passed | Final Step 16 execution log / CI workflow |
| Browser E2E | 6 passed in Chromium | `test-evidence/step-16-playwright-junit.xml` and three Step 16 screenshots |
| Python dependency audit | No known vulnerabilities | Final `pip-audit -r requirements-dev.txt` execution |
| JavaScript dependency audits | Production and complete trees: 0 vulnerabilities | Final `npm audit --omit=dev` and `npm audit` executions |
| Production images | API and web BuildKit builds passed; health/readiness passed | `test-evidence/step-16-demonstration-gate.md` |
| Pull-only Pi Compose | No build sections; API/DB have no host ports; web has one exact LAN bind; backend network is internal | Compose render and packaging contract tests |
| Fresh deterministic demonstration | Seed, normal, peak, anomaly, low-PF, dropout, restart and integrity checks passed locally | `test-evidence/step-16-demonstration-gate.md` |

## Browser flows covered

The final Playwright run used an ephemeral administrator that was removed with
its sessions and audit rows after execution. It verified:

1. all seven authenticated routes and admin controls;
2. client-side invalid-setting rejection without a write request;
3. honest retryable UI when overview APIs are unavailable;
4. a visible WebSocket `Reconnecting` state;
5. 375 px mobile navigation to the Devices workflow; and
6. generic invalid-login feedback without echoing the submitted password.

The run retained:

- `step-16-desktop-settings.png`;
- `step-16-mobile-devices.png`;
- `step-16-api-unavailable.png`; and
- `step-16-playwright-junit.xml`.

## Fresh-volume production rehearsal

A disposable production Compose project was migrated from empty through
revision `0003`. The final script produced five devices, 2,400 initial
measurements, 15 forecasts, one anomaly, two explicit demo alarms, and no
duplicate or cumulative-counter-decrease groups. Power-quality staging added
five rows; dropout staging added 540 rows and left `LOAD-003` older than the
60-second offline threshold. The final manifest was `2945|20|1|2|0`.

Restarting the API returned readiness without changing that manifest. Only
Nginx was host-published. Re-running preparation against the populated volume
was refused without mutation. The disposable containers, network, volume and
temporary environment file were removed after verification.

## Fixed defects and accepted warnings

The complete defect/retest record is
[step-16-defects-retests.md](test-evidence/step-16-defects-retests.md). It
includes the secure-cookie/LAN mismatch, missing ingestion rate limit,
counter-continuity staging, current dependency advisories, and SQLAlchemy 2.1
compatibility.

Two non-failing warnings remain documented:

- Starlette reports that its current TestClient compatibility import will move
  from `httpx` to `httpx2`; this is upstream test tooling and does not affect
  the deployed API.
- Vite reports a 743.07 kB main JavaScript chunk (220.00 kB gzip). The bundle
  passes the prototype build and is recorded as a future code-splitting
  performance item in `limitations.md`.

## Gates that automation cannot pass

The following remain pending and must not be inferred from the results above:

- a timed 7-10 minute student demonstration including alarm acknowledgement
  and visible restart recovery;
- personal explanation, reviewer sign-off and signed AI-use declaration; and
- physical Raspberry Pi 4 clean installation, reboot, clean-volume restore,
  controlled power interruption and target performance/resource evidence.

Use [final-requirements-traceability.md](final-requirements-traceability.md)
for requirement status and [limitations.md](limitations.md) for claim boundaries.
