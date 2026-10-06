# ADR-003: Monitoring-only safety boundary

- Status: Accepted by user at the Step 1 gate on 2026-08-15
- Date: 2026-08-15
- Decision owner: Student/researcher

## Context

The broader research project may eventually study predictive load management. Operating industrial electrical loads introduces hazards, authority questions, fail-safe design, hardware interlocks, and regulatory obligations that are not specified or validated in this dashboard build.

## Options considered

1. Monitoring/advisory only, with no executable control path.
2. Simulated control buttons, which may still create misleading authority and encourage an unsafe future connection.
3. Real commands, which are unacceptable without a separate hardware, safety, authority, and verification specification.

## Decision

The MVP is strictly read-only monitoring and advisory software:

- No enabled Start, Stop, Shed, Restore, relay, contactor, or industrial-load action is implemented in UI, API, WebSocket, simulator, or database command paths.
- Forecasts and anomalies are informational. Future recommendations must be clearly labelled advisory/simulated.
- All roles—including admin—lack load-control permission.
- Real control requires a separate approved safety specification covering hardware interlocks, manual override, fail-safe states, command authentication/authorisation, audit, supervision, hazard analysis, and verification.

## Consequences

- The dashboard can be demonstrated safely using deterministic simulated measurements, forecasts, anomalies, alarms, and connectivity events.
- The project cannot claim implemented automatic load control from this subsystem.
- Any proposed control feature is a safety-boundary change and must stop implementation pending explicit review and a new ADR/specification.
