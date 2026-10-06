# Step 16 student explanation and ownership sign-off

Date prepared: 2026-10-05

## Purpose

The Step 16 gate requires the student to explain the implemented engineering
work without relying on generated prose. This file is a reviewer checklist, not
a pre-completed declaration. Initial and date an item only after a live
explanation, code/evidence navigation, and follow-up question are satisfactory.

## Explanation checklist

| Topic | Student must demonstrate and explain | Student initials/date | Reviewer result/notes |
|---|---|---|---|
| Scope and safety | Why the product is monitoring/advisory only; identify the absence of Start/Stop/Shed/Restore routes and controls. |  |  |
| Architecture | Trace one Overview value from React to versioned API, route, service/repository and PostgreSQL; explain why React does not own formulas. |  |  |
| Data contract | Explain UTC storage, Johannesburg display, unit-bearing field names, null versus zero, data quality, and device/timestamp uniqueness. |  |  |
| Current demand | Hand-calculate a fixture and explain enabled/stale/missing exclusions and the excluded-device count. |  |  |
| Energy today | Explain the local-midnight baseline, positive cumulative-counter deltas, missing baseline and reset segmentation. |  |  |
| Interval/peak demand | Explain time weighting, the configured interval, 90% completeness threshold and why incomplete intervals cannot become a peak. |  |  |
| Completeness | Derive expected/valid counts and gaps; explain why the system does not interpolate missing measurements. |  |  |
| Cost/comparison | Explain Decimal energy x tariff and equal-elapsed-period comparison, including null/zero edge cases. |  |  |
| Simulator | Show seed `118`, stable devices, normal/peak/low-PF/overconsumption/dropout/reset scenarios and why results repeat. |  |  |
| Forecast/anomaly honesty | Explain the fixed simulator forecast formula, confidence bounds, model-version label, 35% anomaly and lack of a trained model. |  |  |
| Alarm demonstration | Derive the 90% and 100% alarm fixture crossings from stored combined demand and limit; state that a continuous production evaluator is not implemented. |  |  |
| Authentication/RBAC/audit | Explain password hashing/session cookie, viewer/operator/admin permissions, acknowledgement attribution, immutable event and secret handling. |  |  |
| Live recovery | Explain heartbeat, sequence, coalescing, five-second loss indication, capped backoff and authoritative REST refetch. |  |  |
| Failure states | Demonstrate loading, empty, error, stale and partial states; explain why API failure cannot display cached values as a live zero. |  |  |
| Tests | Locate one calculation unit test, one API/RBAC test, one component test and one Playwright flow; explain what regression each catches. |  |  |
| Coverage/performance | Explain what line/branch coverage does and does not prove; interpret the retained response-time table without claiming it is physical Pi evidence. |  |  |
| Deployment | Explain ARM64 images, Nginx entry point, internal API/DB network, health/restart/log settings and named volume. |  |  |
| Recovery | Explain backup checksum/catalog validation, clean-volume restore, duplicate check, rollback and why an abrupt-process drill differs from power loss. |  |  |
| Limitations/integration | Identify pending Pi evidence and future gateway, calibrated sensing, ML, rule-engine and safety-case work. |  |  |
| AI use | Describe which work used AI, what was personally inspected/executed/recalculated, rejected suggestions or defects found, and responsibility retained. |  |  |

## Reproduction checks

- [ ] Student starts from a new empty demonstration project/volume.
- [ ] Student follows `docs/demo.md` without an undocumented source edit.
- [ ] Preparation manifest shows 2,400 measurements and zero duplicates.
- [ ] Normal, peak, anomaly, power-quality and dropout evidence is identified.
- [ ] Student acknowledges an alarm and locates the matching audit record.
- [ ] Student restarts the API and explains Reconnecting -> REST recovery.
- [ ] Final manifest and run duration are retained.
- [ ] Student identifies the Step 15 physical Pi checklist status accurately.
- [ ] Student answers reviewer follow-up questions without reading generated
      text verbatim.

## Reviewer decision

- [ ] Pass - all explanations and reproduction checks are satisfactory.
- [ ] Rework required - incomplete topics and retest date are recorded below.

Incomplete topics / defects:

```text

```

Student full name:

Student signature:

Student date (UTC):

Reviewer full name:

Reviewer signature:

Reviewer date (UTC):

This gate remains **pending** while any field above is blank. A generated
signature or an assistant assertion is not acceptable evidence of personal
verification.
