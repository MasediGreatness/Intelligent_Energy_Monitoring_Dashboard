# ADR-001: Fixed application stack

- Status: Accepted by user at the Step 1 gate on 2026-08-15
- Date: 2026-08-15
- Decision owner: Student/researcher

## Context

The dashboard must integrate simulated data now and a Raspberry Pi gateway and machine-learning outputs later. It needs validated APIs, relational/time-filtered storage, responsive charts, repeatable local/Pi deployment, and testable boundaries. The controlling specification prohibits silent substitutions.

## Options considered

1. Python/FastAPI, PostgreSQL/SQLAlchemy/Alembic, React/TypeScript/Vite, native WebSocket, Docker Compose/Nginx.
2. A Python server-rendered UI, which reduces frontend tooling but makes the specified interactive dashboard and typed client boundary less direct.
3. Node.js end to end, which could share a language but diverges from the project's Python/ML ecosystem and the fixed specification.
4. InfluxDB/Grafana, which suits time-series visualisation but does not match the required custom workflows, relational audit/configuration model, roles, or fixed PostgreSQL contract.

## Decision

Adopt the fixed stack:

- Python 3.12, FastAPI, Pydantic, Uvicorn
- PostgreSQL, SQLAlchemy 2, Alembic, Psycopg 3
- React, TypeScript, Vite
- TanStack Query, Recharts, Tailwind CSS
- Native FastAPI WebSocket; REST/PostgreSQL remains authoritative
- Docker Compose and Nginx, with ARM64-compatible images
- Pytest, HTTPX, Ruff, mypy; Vitest, React Testing Library, ESLint, Prettier, Playwright

## Consequences

- The API/data boundary is explicit and OpenAPI can drive frontend types.
- PostgreSQL supports constraints, audit/configuration data, indexed time queries, and Pi ARM64 images.
- Two language/toolchains increase setup and build complexity.
- Native WebSocket logic requires deliberate reconnect, sequence-gap, and coalescing tests.
- Time-series aggregation must be implemented and tested in backend services rather than delegated to Grafana.
- Any replacement of these technologies requires a new approved ADR before code changes.
