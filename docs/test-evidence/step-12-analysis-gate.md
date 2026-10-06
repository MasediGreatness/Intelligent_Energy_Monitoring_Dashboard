# Step 12 History, Forecast and Anomaly gate evidence

Date: 2026-08-16

## Automated checks

- Frontend lint and formatting: passed.
- Frontend Vitest: 18 tests passed across three files.
- Frontend TypeScript and Vite production build: passed.
- Backend Ruff, formatting, and MyPy: passed.
- URL regression changes the History interval, observes `interval=1h` in the
  browser query string, and verifies the subsequent history API query contains
  the same interval.
- CSV fixture verifies UTC ISO timestamps, explicit `active_power_kw` units,
  exact values, sample counts, completeness, CRLF rows, and blank missing data.
- PowerShell's spreadsheet-compatible CSV parser reopened the fixture as two
  rows with all five headings, preserved `2.71`, and preserved missing power as
  blank.
- Aggregation tests force 15-minute buckets for a seven-day range and hourly
  buckets for a 31-day range.
- The no-forecast test requires the exact `Model data unavailable` state.

## Performance evidence

- A live 31-day, five-device hourly query completed in 0.241 seconds.
- The response contained five series and 3,725 total buckets, keeping chart
  input bounded rather than requesting raw samples.

## Live browser review

- History rendered per-device power, daily energy, and 15-minute demand from
  backend buckets, with incomplete-bucket counts visible.
- Changing interval from `15m` to `1h` produced the shareable URL
  `?from=2026-08-09&to=2026-08-16&device=all&interval=1h`.
- A decimal-string chart defect found during review was fixed by numeric
  conversion and per-device pivoting; no energy was recalculated in React.
- Exactly 215 resolved ingestion-test artifacts with constant 2.71 kW and
  synthetic billion-scale counters were removed from development `LOAD-001`;
  its last-seen timestamp was restored from remaining measurements.
- The documented deterministic `sudden_overconsumption` scenario added 300
  measurements, five simulator forecasts, and one clearly simulated anomaly.
- Forecast rendered actual/forecast series, confidence band, and model version
  `simulator-v1-seed-118`.
- The anomaly timeline showed type, metric, expected value, actual value, score,
  severity, explanation, status, and timestamp.
- Selecting the unavailable 24-hour horizon updated the URL and displayed
  `Model data unavailable` without inventing a prediction.

## Gate result

The Step 12 gate checks pass. The user accepted ADR-009 and the rendered
analysis/export behavior before Step 13 began.
