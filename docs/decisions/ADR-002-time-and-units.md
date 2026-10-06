# ADR-002: UTC time, SI units, numeric meaning, and missing data

- Status: Accepted by user at the Step 1 gate on 2026-08-15
- Date: 2026-08-15
- Decision owner: Student/researcher

## Context

Energy calculations drift when timestamps, timezones, units, precision, reset handling, or missing values are interpreted differently across the gateway, database, backend, and browser.

## Options considered

1. Store UTC instants with explicit SI-unit field names and convert only for display/calculation boundaries.
2. Store local wall-clock time, which is convenient locally but ambiguous and weakens integration/reproducibility.
3. Use zero for missing samples, which is simple but falsely lowers demand/energy and makes outages look like valid measurements.

## Decision

- Store only timezone-aware timestamps in PostgreSQL `TIMESTAMPTZ` and serialize ISO 8601 UTC with `Z`.
- Display Africa/Johannesburg by default; local-day calculations explicitly apply the configured timezone.
- Use unit-bearing field names: `_v`, `_a`, `_kw`, `_kvar`, `_kva`, `_hz`, `_kwh_total`.
- Use database double precision for sampled electrical values and decimal/numeric for cumulative energy and tariffs.
- Treat cumulative energy as a monotonic meter within a segment. A documented reset starts a new segment; no subtraction occurs across a reset.
- Represent missing values as `NULL` with explicit `data_quality`; never substitute numeric zero.
- Apply the specified UI precision without changing stored meaning.

## Consequences

- All producers must send timezone-aware timestamps and the backend must reject naive timestamps.
- Local-midnight and equal-period calculations require explicit timezone conversion and boundary tests.
- Reset/gap/completeness metadata becomes part of honest reporting.
- The frontend formats values but does not recalculate engineering totals.
