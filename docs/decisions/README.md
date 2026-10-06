# Architecture Decision Record Index

ADRs preserve the reasoning that keeps the dashboard, API, database, and
deployment aligned. An accepted ADR is normative together with the controlling
specification; implementation details must not silently contradict it.

| ADR | Decision | Status | Contract area |
|---|---|---|---|
| [ADR-001](ADR-001-stack.md) | Fixed application stack | Accepted | Technology and repository boundaries |
| [ADR-002](ADR-002-time-and-units.md) | UTC time, SI units, numeric meaning, missing data | Accepted | Storage/API/UI data meaning |
| [ADR-003](ADR-003-monitoring-only-safety-boundary.md) | Monitoring-only safety boundary | Accepted | No real load control |
| [ADR-004](ADR-004-calculation-boundaries.md) | Calculation validity and gap boundaries | Accepted | Energy, demand, peak, completeness |
| [ADR-005](ADR-005-authentication-and-roles.md) | Opaque sessions and fixed roles | Accepted | Authentication/authorization |
| [ADR-006](ADR-006-live-recovery-protocol.md) | Sequenced live updates with REST recovery | Accepted | WebSocket/reconnect consistency |
| [ADR-007](ADR-007-dashboard-shell-and-design-system.md) | Responsive shell and design system | Accepted | Navigation, states, accessibility |
| [ADR-008](ADR-008-api-authoritative-dashboard-values.md) | API-authoritative dashboard values | Accepted | Backend/frontend calculation boundary |
| [ADR-009](ADR-009-shareable-analysis-and-csv-contract.md) | Shareable filters and CSV contract | Accepted | Analysis URL/export reproducibility |
| [ADR-010](ADR-010-operational-write-contract.md) | Alarm, device, and settings writes | Accepted | Mutation lifecycle and audit |

## Decision ownership

The student/researcher owns acceptance and must be able to explain the context,
alternatives, decision, consequences, and evidence for each record. AI-generated
wording does not transfer engineering responsibility.

## When to add or supersede an ADR

Create a new ADR before implementing a material change to any of these areas:

- framework, database, deployment, or live-channel technology;
- public route, field, unit, enum, pagination, or error meaning;
- timestamp/timezone, missing-data, reset, aggregation, or formula semantics;
- role, session, secret, audit, or network trust boundary;
- simulator/gateway/ML boundary;
- status color/text meaning, primary routes, or accessibility contract;
- monitoring-only safety scope or any proposed control path.

An ADR should contain: status/date/owner, context, viable options, decision,
consequences, compatibility/migration impact, and required verification. Do not
rewrite an accepted historical decision to hide a change; mark it superseded and
link the replacement.

## Contract-change checklist

For a fixed-contract change, update and verify all applicable artifacts:

1. controlling requirement/approved ADR;
2. SQLAlchemy model and forward/backward Alembic migration;
3. Pydantic request/response schema and error behavior;
4. generated `apps/api/openapi.json` and frontend TypeScript types;
5. backend services/repositories and React consumers;
6. unit, integration, component, E2E, migration, and compatibility tests;
7. data dictionary, API contract, architecture, limitations, and traceability;
8. deployment/rollback and retained evidence.

The [architecture](../architecture.md), [data dictionary](../data-dictionary.md),
and [API contract](../api-contract.md) consolidate the current accepted outcome.
