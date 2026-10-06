# ADR-010: Operational write and settings contract

- Status: Accepted at the Step 13 gate
- Date: 2026-08-16

## Decision

Alarm acknowledgement is a one-time transition from `open` to
`acknowledged`. Operators and administrators may perform it with a required
note. The API records the authenticated user's UUID and current UTC time on the
alarm and appends an `alarm.acknowledged` event. Cleared or previously
acknowledged alarms reject the transition instead of overwriting attribution.

Only administrators may create or update devices. Codes are normalized to
uppercase and contain only letters, digits, `_`, or `-`; rated power must be
greater than zero and at most 2000 kW. Devices are retired by setting
`enabled=false`. There is deliberately no device delete endpoint or dashboard
delete action, preserving measurements, forecasts, anomalies, alarms, and
audit history.

The settings table contains exactly these operational keys and constraints:

| Key | Contract |
|---|---|
| `demand_limit_kw` | Number greater than 0 and at most 2000 |
| `demand_interval_minutes` | Integer: 1, 5, 15, 30, or 60 |
| `tariff_zar_per_kwh` | Number from 0 through 100 |
| `timezone` | Valid IANA timezone; UI offers Johannesburg and UTC |
| `online_timeout_seconds` | Integer from 1 through 86400 |
| `stale_timeout_seconds` | Integer from 1 through 86400 and greater than online timeout |
| `simulator_profile` | One of the six documented simulator profiles |

Migration `0003` creates the seven default rows. The API is authoritative for
validation and appends `setting.updated`, `device.created`, or
`device.updated` events after successful writes. The UI applies the same
limits for early feedback, performs no optimistic write, and refetches the
authoritative resource after every successful mutation.

## Consequences

- Alarm attribution cannot silently move from one operator to another.
- Device history remains queryable after monitoring is disabled.
- Unknown settings and invalid cross-field timeout states cannot enter through
  the API.
- Direct API calls enforce the same role boundary as hidden dashboard controls.
- Any new setting key, simulator profile, device field, or lifecycle transition
  requires a coordinated contract, migration, generated-client, and test
  change.
