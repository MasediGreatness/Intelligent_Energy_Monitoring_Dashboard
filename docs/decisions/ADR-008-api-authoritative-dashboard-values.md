# ADR-008: API-authoritative dashboard values and live refresh

- Status: Accepted at the Step 11 gate
- Date: 2026-08-16

## Decision

The Overview KPI cards display values from `/api/v1/dashboard/summary` without
recalculating demand, energy, peak demand, alarm counts, exclusions, or
completeness in React. The API calculates demand change against 15 minutes
earlier and energy change against yesterday at the same local elapsed time.

Charts render server-produced history buckets and forecast records. The UI may
sum aligned per-device power buckets to draw the documented total-power line,
but that display transformation must never become an alternative KPI, energy,
or peak-demand calculation.

The WebSocket remains an acceleration channel: measurement and device events
invalidate latest-measurement, summary, and chart queries; alarm events
invalidate summary and recent-alarm queries. REST responses remain
authoritative after each event, reconnect, or sequence gap.

Missing numeric values display `-`; stale, offline, partial, no-data, loading,
and error states remain explicit. A last known value may be shown only beside
its timestamp and non-live status.

## Consequences

- KPI and engineering formulas remain testable in one backend source of truth.
- Live pages converge on committed database state rather than trusting an event
  payload as permanent state.
- UI tests can prove exact API-to-card rendering without duplicating formulas.
- Backend response-field changes require coordinated schema and UI updates.
