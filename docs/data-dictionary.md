# Data Dictionary

## Authority and conventions

This dictionary explains the implemented schema and engineering meaning. The
SQLAlchemy models, Alembic migrations, Pydantic schemas, generated OpenAPI file,
and accepted ADRs are the executable authorities. A change to a name, unit,
range, enum, relationship, or calculation meaning requires coordinated schema,
migration, API, generated-client, test, and documentation updates.

Common rules:

- UUIDs identify user-facing entities. BIGSERIAL identifies high-volume or
  append-only rows.
- Every stored timestamp is PostgreSQL `TIMESTAMPTZ` and every API timestamp is
  ISO 8601 with a UTC offset (`Z` for UTC).
- Local-day calculations use the configured IANA timezone, normally
  `Africa/Johannesburg`; storage remains UTC.
- Field suffixes state SI units: `_v`, `_a`, `_kw`, `_kvar`, `_kva`, `_hz`, and
  `_kwh_total`.
- Sampled electrical values use double precision. Cumulative energy uses
  `NUMERIC(18,6)` and calculations use Decimal where monetary/cumulative
  precision matters.
- `NULL` plus `data_quality` represents missing data. Numeric zero is a real
  measurement and must never be substituted for missing data.
- Cumulative energy is monotonic only within a meter segment. An explicit reset
  starts a new segment; calculations do not subtract across a reset.

## Enumerations

| Name | Values | Meaning |
|---|---|---|
| `user_role` | `viewer`, `operator`, `admin` | Ordered dashboard authority |
| `phase_type` | `single_phase`, `three_phase` | Device supply category |
| `criticality` | `low`, `medium`, `high`, `critical` | Operational importance |
| `data_quality` | `good`, `suspect`, `missing` | Producer assessment of the sample |
| `severity` | `low`, `medium`, `high`, `critical` | Alarm/anomaly consequence level |
| `alarm_status` | `open`, `acknowledged`, `cleared` | Alarm lifecycle |
| `anomaly_status` | `open`, `reviewed`, `cleared` | Anomaly review lifecycle |
| derived device status | `online`, `stale`, `offline`, `disabled` | Calculated at read time; not persisted as a device column |

## Persisted tables

### `users`

| Field | Database type | Null | Meaning/constraint |
|---|---|---:|---|
| `id` | UUID PK | No | User identity |
| `email` | VARCHAR(320), unique | No | Normalized login address; never a password identifier exposed in logs with a secret |
| `password_hash` | VARCHAR(255) | No | Argon2id hash; plaintext is never persisted |
| `role` | `user_role` | No | Fixed role used by backend dependencies |
| `is_active` | BOOLEAN | No | Disabled users cannot authenticate |
| `created_at` | TIMESTAMPTZ | No | Database creation time |
| `last_login_at` | TIMESTAMPTZ | Yes | Most recent successful login |

Users are created only through the explicit setup CLI. Migrations and startup
never seed a default credential.

### `auth_sessions`

This internal table was added in migration `0002` to implement revocable opaque
browser sessions.

| Field | Database type | Null | Meaning/constraint |
|---|---|---:|---|
| `id` | UUID PK | No | Session row identity |
| `user_id` | UUID FK -> `users.id`, indexed | No | Session owner |
| `token_hash` | VARCHAR(64), unique | No | SHA-256 hash of the random token; raw token exists only in the cookie |
| `created_at` | TIMESTAMPTZ | No | Issue time |
| `expires_at` | TIMESTAMPTZ, indexed | No | Absolute expiry checked by the API |
| `revoked_at` | TIMESTAMPTZ | Yes | Logout/revocation time; non-null means unusable |

### `devices`

| Field | Database type | Null | Meaning/constraint |
|---|---|---:|---|
| `id` | UUID PK | No | Stable internal device identity |
| `code` | VARCHAR(64), unique | No | Stable producer identifier; write API normalizes uppercase and permits `A-Z`, `0-9`, `_`, `-` |
| `name` | VARCHAR(160) | No | Operator-facing name |
| `location` | VARCHAR(255) | No | Physical/functional location description |
| `phase_type` | `phase_type` | No | Single- or three-phase category |
| `rated_power_kw` | DOUBLE PRECISION | No | Nameplate active power; greater than 0, write API maximum 2000 kW |
| `criticality` | `criticality` | No | Operational importance |
| `enabled` | BOOLEAN | No | Whether included in monitoring; disabling preserves history |
| `last_seen_at` | TIMESTAMPTZ | Yes | Timestamp of most recent accepted measurement |
| `created_at` | TIMESTAMPTZ | No | Creation time |

There is no device DELETE route. `enabled=false` is the retirement operation.

### `measurements`

| Field | Database type | Null | Unit/range and meaning |
|---|---|---:|---|
| `id` | BIGSERIAL PK | No | Storage row identity |
| `device_id` | UUID FK -> `devices.id` | No | Resolved from public `device_code` |
| `measured_at` | TIMESTAMPTZ | No | Source sample instant; unique with device; no more than five minutes in the future |
| `voltage_v` | DOUBLE PRECISION | Yes | RMS/declared voltage, 0-1000 V |
| `current_a` | DOUBLE PRECISION | Yes | Current, 0-2000 A |
| `active_power_kw` | DOUBLE PRECISION | Yes | Active power, -2000 to 2000 kW; negative reserved for export/generation |
| `reactive_power_kvar` | DOUBLE PRECISION | Yes | Reactive power in kvar |
| `apparent_power_kva` | DOUBLE PRECISION | Yes | Apparent power in kVA |
| `power_factor` | DOUBLE PRECISION | Yes | Ratio from 0.00 to 1.00 |
| `frequency_hz` | DOUBLE PRECISION | Yes | Hard range 40-70 Hz; values outside 45-55 Hz require `suspect` quality at ingestion |
| `energy_kwh_total` | NUMERIC(18,6) | Yes | Non-negative cumulative meter counter in kWh |
| `data_quality` | `data_quality` | No | `good`, `suspect`, or `missing` |

The unique constraint on `(device_id, measured_at)` is the idempotency boundary.
The API accepts an `energy_reset` boolean as transport-only metadata; it is not a
measurement column and results in an explicit reset event rather than a silent
counter decrease.

Indexes:

- `(device_id, measured_at DESC)` for per-device series;
- `(measured_at DESC)` for recent/aggregate queries.

### `forecasts`

| Field | Database type | Null | Meaning |
|---|---|---:|---|
| `id` | BIGSERIAL PK | No | Forecast row identity |
| `device_id` | UUID FK -> `devices.id` | Yes | Device scope; null represents site/aggregate scope |
| `generated_at` | TIMESTAMPTZ | No | Forecast production time |
| `target_at` | TIMESTAMPTZ | No | Predicted instant |
| `horizon_minutes` | INTEGER | No | Positive minutes from generation to target horizon |
| `predicted_power_kw` | DOUBLE PRECISION | No | Predicted active power |
| `lower_kw` | DOUBLE PRECISION | Yes | Lower confidence/uncertainty bound |
| `upper_kw` | DOUBLE PRECISION | Yes | Upper confidence/uncertainty bound; cannot be below lower bound |
| `model_version` | VARCHAR(128) | No | Producer/model identifier; simulator values are visibly labelled `simulator-*` |

Index: `(target_at, generated_at DESC)` supports current-curve selection. The
implemented simulator produces contract-shaped placeholders, not a trained ML
model result.

### `anomalies`

| Field | Database type | Null | Meaning |
|---|---|---:|---|
| `id` | UUID PK | No | Anomaly identity |
| `device_id` | UUID FK -> `devices.id` | No | Affected device |
| `detected_at` | TIMESTAMPTZ | No | Detection instant |
| `anomaly_type` | VARCHAR(100) | No | Stable category |
| `severity` | `severity` | No | Consequence classification |
| `metric` | VARCHAR(100) | No | Compared metric name |
| `actual_value` | DOUBLE PRECISION | Yes | Observed value, unit determined by metric |
| `expected_value` | DOUBLE PRECISION | Yes | Expected value on the same unit basis |
| `score` | DOUBLE PRECISION | No | Producer-supplied anomaly score |
| `explanation` | TEXT | No | Human-readable reason/context |
| `status` | `anomaly_status` | No | `open`, `reviewed`, or `cleared` |

Index: `(status, detected_at DESC)` supports the operational list.

### `alarms`

| Field | Database type | Null | Meaning |
|---|---|---:|---|
| `id` | UUID PK | No | Alarm identity |
| `device_id` | UUID FK -> `devices.id` | Yes | Affected device; null permits site/system alarms |
| `source` | VARCHAR(100) | No | Originating rule/service |
| `alarm_type` | VARCHAR(100) | No | Stable alarm category |
| `severity` | `severity` | No | Consequence classification |
| `message` | TEXT | No | Operator-facing message |
| `triggered_at` | TIMESTAMPTZ | No | Alarm creation instant |
| `acknowledged_at` | TIMESTAMPTZ | Yes | First successful acknowledgement time |
| `acknowledged_by` | UUID FK -> `users.id` | Yes | Authenticated operator/admin attribution |
| `acknowledgement_note` | TEXT | Yes | Required non-blank note when acknowledging |
| `cleared_at` | TIMESTAMPTZ | Yes | Condition-clear instant |
| `status` | `alarm_status` | No | `open`, `acknowledged`, or `cleared` |

Acknowledgement is a one-time `open -> acknowledged` transition. A repeat or
cleared acknowledgement returns conflict and cannot replace attribution. Index:
`(status, severity, triggered_at DESC)`.

### `settings`

| Field | Database type | Null | Meaning |
|---|---|---:|---|
| `key` | VARCHAR(100) PK | No | One of exactly seven supported operational keys |
| `value_json` | JSON | No | Typed scalar validated by the service |
| `description` | TEXT | No | Operator-facing explanation |
| `updated_at` | TIMESTAMPTZ | No | Committed update time |
| `updated_by` | UUID FK -> `users.id` | Yes | Administrator who made the update; null for migration defaults |

Migration `0003` creates these rows:

| Key | Default | Accepted values |
|---|---:|---|
| `demand_limit_kw` | `50.0` | Number greater than 0 and at most 2000 kW |
| `demand_interval_minutes` | `15` | Integer `1`, `5`, `15`, `30`, or `60` |
| `tariff_zar_per_kwh` | `3.0` | Number from 0 through 100 ZAR/kWh |
| `timezone` | `Africa/Johannesburg` | Valid IANA timezone name |
| `online_timeout_seconds` | `10` | Integer 1-86400 |
| `stale_timeout_seconds` | `60` | Integer 1-86400 and greater than online timeout |
| `simulator_profile` | `normal` | One of the six documented simulator scenarios |

Successful changes append a `setting.updated` event containing non-secret old
and committed values.

### `system_events`

| Field | Database type | Null | Meaning |
|---|---|---:|---|
| `id` | BIGSERIAL PK | No | Event identity |
| `event_at` | TIMESTAMPTZ | No | Database event time |
| `actor_user_id` | UUID FK -> `users.id` | Yes | Authenticated human actor where applicable |
| `event_type` | VARCHAR(100) | No | Stable event name such as login, acknowledgement, reset, or update |
| `entity_type` | VARCHAR(100) | Yes | Target category |
| `entity_id` | VARCHAR(128) | Yes | Target identity as text |
| `details_json` | JSON | No | Non-secret structured context |

The application treats this table as append-only. Passwords, raw sessions,
ingest secrets, and application secret keys are prohibited from event details
and logs. Index: `(event_at DESC)`.

## Derived metric definitions

| Metric | Authoritative rule |
|---|---|
| Device online | Enabled and latest record age <= `online_timeout_seconds` |
| Device stale | Enabled and age > online timeout but <= `stale_timeout_seconds` |
| Device offline | Enabled with no record or age > stale timeout |
| Device disabled | `enabled=false`; reported separately |
| Current demand | Sum latest usable `active_power_kw` only for enabled, non-stale devices; return exclusions |
| Energy today | Sum valid cumulative-counter segments from the local-midnight boundary; expose baseline gaps and resets |
| Interval demand | Time-weighted mean active power over the configured window; a value covers at most one expected sample interval |
| Peak demand | Maximum interval demand in the local day among windows with at least 90% completeness |
| Previous comparison | Current and previous periods use equal local elapsed time |
| Estimated cost | Valid `energy_kwh * tariff_zar_per_kwh` using Decimal; label as estimate in ZAR |
| Completeness | `valid_samples / expected_samples * 100`; expose gaps and never silently interpolate |

Both `good` and `suspect` samples may contribute to calculations; `missing` or
null metric values may not. A counter baseline at/before local midnight is
recent when no more than one configured demand interval before the boundary;
otherwise a first post-midnight value may be used with `baseline_gap=true`.

## Query bucket contract

History supports `raw`, `10s`, `1m`, `15m`, `1h`, and `1d`. Every aggregate
point contains:

| Field | Meaning |
|---|---|
| `bucket_at` | UTC start of the bucket |
| `value` | Aggregated requested metric, nullable |
| `sample_count` | Contributing samples |
| `completeness_pct` | Expected-versus-valid coverage, 0-100 |

Raw history is limited to 24 hours and all history requests to 31 days. The
browser applies stricter minimum aggregation for long chart ranges.

## Frontend display precision

Formatting does not change stored meaning:

| Quantity | Display |
|---|---|
| kW, kWh, voltage | One decimal place |
| Current | Two decimal places |
| Power factor, frequency | Two decimal places |
| Missing numeric value | `-`, accompanied by quality/state where relevant |

All charts label axes with units and time tooltips show absolute timestamps;
status also includes text/icon semantics rather than color alone.
