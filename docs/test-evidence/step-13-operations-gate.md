# Step 13 Alarms, Devices and Settings gate evidence

Date: 2026-08-16

## Automated checks

- Backend Pytest: 71 tests passed.
- Backend Ruff and formatting: passed.
- Backend MyPy: passed for 52 source files.
- Frontend Vitest: 22 tests passed across three files.
- Frontend ESLint and Prettier: passed.
- Frontend TypeScript and Vite production build: passed.
- The exported OpenAPI document validates and the generated TypeScript client
  was refreshed from it.
- Alarm tests prove the acknowledgement response and stored alarm contain the
  current operator UUID, UTC timestamp, note, and matching append-only audit
  event.
- Role tests prove viewers and operators receive HTTP 403 for device writes;
  viewers receive HTTP 403 for acknowledgement; operators receive HTTP 403 for
  settings writes.
- Device tests prove admin create, edit, and disable; the disabled status is
  returned, audit events exist, and `DELETE /devices/{id}` returns 405.
- Settings tests prove negative demand and an invalid timeout relationship
  return the standard HTTP 422 error without changing stored values.
- Frontend interaction tests prove non-admin controls are absent, admin device
  controls are present, invalid settings issue no PATCH, and an operator
  acknowledgement refetches the alarm list.

## Migration and live browser review

- Alembic revision `0003` was applied to the test and development databases;
  readiness reports the single head.
- The administrator settings form loaded all seven seeded keys. A tariff write
  persisted, refetched, and was restored to 3.0 ZAR/kWh.
- `LOAD-001` metadata was edited and restored. It was then disabled, remained
  visible with status `disabled`, and was re-enabled. No delete action appeared.
- A clearly labelled `step13-live-review` alarm was created for review. The
  table filtered and paginated it, its detail drawer rendered its complete
  context, and the administrator acknowledged it with a note.
- Direct database verification showed status `acknowledged`, a non-null UTC
  time, `admin@intelligentenergy.com` attribution, the exact note, an
  `alarm.acknowledged` event, and identical alarm/audit actor UUIDs.
- Desktop visual inspection confirmed the table, filters, drawer, forms,
  feedback, navigation state, and monitoring-only boundary remain usable.

## Gate result

The Step 13 gate checks pass. The user accepted ADR-010 and the rendered
operational workflows before Step 14 began.
