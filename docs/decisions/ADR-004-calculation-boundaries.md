# ADR-004: Calculation validity and gap boundaries

- Status: Accepted by user at the Step 6 gate on 2026-08-15
- Date: 2026-08-15
- Decision owner: Student/researcher

## Context

The specification fixes metric meanings but leaves three operational tolerances to be explicit: how long a meter baseline remains usable, how sampled power covers time, and when an incomplete demand interval may qualify as a daily peak.

## Decision

- A counter baseline at or before local midnight is considered recent when it is no more than the configured demand interval (15 minutes by default) before the boundary. A later first sample may be used but the result is marked `baseline_gap=true`.
- A valid sampled power value covers at most one expected sample interval. It is never carried across a longer gap; missing coverage is exposed through completeness.
- Time-weighted demand divides by valid covered seconds and returns completeness independently. It therefore never converts missing time to zero and never silently interpolates it.
- A demand interval must have at least 90% completeness to qualify for daily peak selection. This threshold should become configurable if field evidence supports another value.
- `good` and `suspect` samples may contribute; `missing` samples and null values may not.
- Estimated cost is a Decimal calculation using the configured flat ZAR tariff and is explicitly an estimate.

## Consequences

Short gaps reduce completeness instead of lowering power. A panel can display partial data while excluding insufficient intervals from peak selection. Hardware sampling evidence may justify a later ADR revising the baseline or peak-completeness tolerances.
