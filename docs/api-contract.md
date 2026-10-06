# REST and WebSocket API Contract

## Authority and compatibility rule

The stable application prefix is `/api/v1`. `/health` and `/ready` are the two
unversioned operational exceptions. The committed machine-readable authority is
`apps/api/openapi.json`; frontend types are generated from it into
`apps/web/src/api/generated.ts` with `npm run generate:api`.

A route, method, field name, unit, enum, status code, role, or query-limit change
is a coordinated contract change. Update the backend schema, OpenAPI document,
generated TypeScript types, tests, this file, and an ADR where architectural
meaning changes.

Development exposes interactive OpenAPI at `/docs`. Production Nginx does not
publish that unversioned path; the API container is internal-only.

## Authentication and transport

### Browser session

`POST /api/v1/auth/login` accepts an email and password, verifies an Argon2id
hash, creates a random opaque session, and returns only the user identity and
expiry in JSON. The raw token is sent in the `energy_session` cookie:

- `HttpOnly`
- `SameSite=Strict`
- path `/api/v1`
- bounded by `AUTH_SESSION_MINUTES` (30 minutes by default)
- `Secure` controlled explicitly by `SESSION_COOKIE_SECURE`

Local/private-LAN HTTP sets `SESSION_COOKIE_SECURE=false`; an HTTPS-terminated
deployment must set it to `true`. The supplied Nginx configuration does not
provide TLS. Raw tokens are never stored: PostgreSQL contains only their SHA-256
hash, expiry, and revocation time. Logout revokes the row and expires the cookie.

Login is rate-limited to 10 attempts/minute per client. Ingestion is rate-limited
to 120 requests/minute per client, which permits one-second delivery while
bounding abusive request bursts. Authentication success,
failure, and logout are audit events without passwords or raw tokens.

### Machine ingestion

Measurement producers authenticate independently with `X-Ingest-Key`. A
browser cookie does not grant ingestion authority, and the ingest key does not
grant dashboard access. Ingestion is rate-limited to 120 requests/minute per
client in addition to the 60-record batch limit.

## Role permissions

| Action | Viewer | Operator | Admin |
|---|:---:|:---:|:---:|
| Read dashboard/data and export CSV | Yes | Yes | Yes |
| Subscribe to live events | Yes | Yes | Yes |
| Acknowledge an alarm | No | Yes | Yes |
| Create/update a device | No | No | Yes |
| Update a setting | No | No | Yes |
| Send a load-control command | Not implemented | Not implemented | Not implemented |

Unauthenticated dashboard requests return 401. An authenticated but insufficient
role returns 403. Hiding a control in React is not the security boundary; the
FastAPI dependency enforces it for direct calls.

## Endpoint inventory

| Method | Route | Authentication | Purpose |
|---|---|---|---|
| GET | `/health` | None | Process liveness only; no database dependency |
| GET | `/ready` | None | Database reachable and Alembic at the single current head |
| POST | `/api/v1/auth/login` | Credentials in body | Issue opaque session cookie |
| POST | `/api/v1/auth/logout` | Session | Revoke current session |
| GET | `/api/v1/auth/me` | Session | Return current `id`, `email`, `role` |
| POST | `/api/v1/ingest/measurements` | `X-Ingest-Key` | Validate/idempotently ingest 1-60 records |
| GET | `/api/v1/dashboard/summary` | Session | Authoritative KPIs, alarm/device counts, completeness |
| GET | `/api/v1/measurements/latest` | Session | Latest value/status for all or selected devices |
| GET | `/api/v1/measurements/history` | Session | Bounded raw/aggregate measurement series |
| GET | `/api/v1/energy/daily` | Session | Per-device daily energy, peak, completeness |
| GET | `/api/v1/forecasts/latest` | Session | Latest generated forecast curve for a horizon |
| GET | `/api/v1/anomalies` | Session | Filtered/paginated anomalies |
| GET | `/api/v1/alarms` | Session | Filtered/paginated alarms |
| PATCH | `/api/v1/alarms/{alarm_id}/acknowledge` | Operator/admin | One-time acknowledgement with note |
| GET | `/api/v1/devices` | Session | Paginated devices with derived status |
| POST | `/api/v1/devices` | Admin | Create device |
| PATCH | `/api/v1/devices/{device_id}` | Admin | Update/disable device; no hard delete |
| GET | `/api/v1/settings` | Session | Read seven fixed operational settings |
| PATCH | `/api/v1/settings/{key}` | Admin | Validate/update one fixed setting |
| GET | `/api/v1/events` | Session | Paginated immutable audit/system history |
| WS | `/api/v1/ws/live` | Session cookie | Sequenced live notifications and heartbeat |

## Common list and error envelopes

Paginated lists use:

```json
{
  "page": 1,
  "page_size": 50,
  "total": 137,
  "items": []
}
```

`page` starts at 1; `page_size` is 1-200 and defaults to 50.

Known application and request-validation errors use:

```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "The end timestamp must be after the start timestamp.",
    "details": {"field": "to"},
    "request_id": "01J5..."
  }
}
```

Clients may use `code` for stable handling and `message` for display. They must
not parse human text for logic. `request_id` correlates the response and
structured logs. Secret values are never included in `details`.

Common status meanings:

| Status | Meaning |
|---:|---|
| 200 | Successful read/update/login/logout |
| 201 | Device created |
| 202 | Authenticated ingestion batch processed, possibly with per-record rejects/duplicates |
| 401 | Missing/invalid browser session or ingest key |
| 403 | Valid user lacks the required role |
| 404 | Requested entity does not exist |
| 409 | State/uniqueness conflict, such as repeated acknowledgement or device code |
| 422 | Query/body/settings validation failure |
| 429 | Login or ingestion request rate limit exceeded |

## Measurement ingestion

`POST /api/v1/ingest/measurements`

Headers:

```http
Content-Type: application/json
X-Ingest-Key: <secret>
```

Body:

```json
{
  "source": "gateway",
  "records": [
    {
      "device_code": "LOAD-001",
      "measured_at": "2026-08-15T19:30:00Z",
      "voltage_v": 231.4,
      "current_a": 12.63,
      "active_power_kw": 2.71,
      "reactive_power_kvar": 0.74,
      "apparent_power_kva": 2.81,
      "power_factor": 0.96,
      "frequency_hz": 49.99,
      "energy_kwh_total": 1842.376,
      "data_quality": "good",
      "energy_reset": false
    }
  ]
}
```

- `source` is `simulator` or `gateway`.
- Batch length is 1-60.
- All measurement fields except `device_code`, `measured_at`, and
  `data_quality` are nullable so missing data is not converted to zero.
- `energy_reset` is optional transport metadata (default false). It is removed
  before persistence and is not a simulator-only measurement column.
- Unknown extra fields are rejected.
- Timestamps must be timezone-aware and no more than five minutes in the future.
- Full range/meaning rules are in the [data dictionary](data-dictionary.md).

Authenticated, well-formed batches return HTTP 202:

```json
{
  "accepted_count": 58,
  "duplicate_count": 1,
  "rejected_count": 1,
  "errors": [
    {"record_index": 59, "field": "power_factor", "reason": "..."}
  ]
}
```

A duplicate is not a second accepted row; uniqueness is
`(device_id, measured_at)`. Invalid authentication or malformed batch JSON
rejects the whole request. Otherwise each record has an independent outcome, so
one bad record cannot corrupt or mislabel another.

## Read query contracts

| Route | Query parameters and limits |
|---|---|
| `/dashboard/summary` | `timezone` (IANA; default `Africa/Johannesburg`) |
| `/measurements/latest` | repeatable optional `device_id` UUID |
| `/measurements/history` | repeatable required `device_id`; required `from`, `to`, `interval`, `metric`; optional `timezone` default UTC |
| `/energy/daily` | required `from_date`, `to_date`; optional `device_id`; `timezone` default UTC |
| `/forecasts/latest` | required positive `horizon_minutes`; optional `device_id` |
| `/anomalies` | `status`, `severity`, `device_id`, `from`, `to`, `page`, `page_size` |
| `/alarms` | `status`, `severity`, `device_id`, `from`, `to`, `page`, `page_size` |
| `/devices` | `enabled`, `page`, `page_size` |
| `/events` | `event_type`, `page`, `page_size` |

History intervals are `raw`, `10s`, `1m`, `15m`, `1h`, `1d`. Metrics are
`voltage_v`, `current_a`, `active_power_kw`, `reactive_power_kvar`,
`apparent_power_kva`, `power_factor`, `frequency_hz`, or `energy_kwh_total`.
Each point returns `bucket_at`, nullable `value`, `sample_count`, and
`completeness_pct`. Any history request is limited to 31 days; `raw` is limited
to 24 hours. Date ranges are half-open (`from <= timestamp < to`) where the
route operates on instants.

Alarm statuses are `open`, `acknowledged`, `cleared`; anomaly statuses are
`open`, `reviewed`, `cleared`; shared severities are `low`, `medium`, `high`,
`critical`.

## Dashboard summary

`GET /api/v1/dashboard/summary` returns values calculated in backend services:

```json
{
  "generated_at": "2026-08-15T19:30:02Z",
  "timezone": "Africa/Johannesburg",
  "current_demand_kw": 42.8,
  "current_demand_change_pct": 4.2,
  "energy_today_kwh": 318.4,
  "energy_vs_previous_pct": -3.8,
  "peak_demand_kw": 49.2,
  "peak_demand_at": "2026-08-15T14:15:00Z",
  "demand_limit_kw": 50.0,
  "active_alarms": {"critical": 0, "high": 1, "medium": 1, "low": 0},
  "devices": {"online": 4, "stale": 1, "offline": 0, "disabled": 1},
  "data_completeness_pct": 99.3,
  "excluded_stale_devices": 1
}
```

Nullable values remain null when unavailable. The browser displays `-` and an
explicit state; it does not replace null with zero or recompute a KPI.

## Protected writes

### Alarm acknowledgement

`PATCH /api/v1/alarms/{alarm_id}/acknowledge`

```json
{"note": "Investigated at panel; reading confirmed."}
```

The note is trimmed, 1-2000 characters, and required. A successful call records
the current UTC time and authenticated operator/admin UUID, appends
`alarm.acknowledged`, publishes `alarm.changed` after commit, and returns the
complete alarm inside `{ "alarm": ... }`. Repeated or cleared transitions return
409 and do not overwrite attribution.

### Device creation/update

Device fields are `code`, `name`, `location`, `phase_type`, `rated_power_kw`,
`criticality`, and `enabled`. Create requires every field except `enabled`
(default true); patch requires at least one non-null field. Codes normalize to
uppercase and match `^[A-Z0-9][A-Z0-9_-]{0,63}$`; rated power is `(0, 2000]`.
Code conflict returns 409. There is no DELETE route: patch `enabled=false`.
Successful writes append `device.created`/`device.updated` and return
`{ "device": ... }`.

### Setting update

`PATCH /api/v1/settings/{key}` accepts `{ "value": ... }`. Only the seven keys
and validation rules in the [data dictionary](data-dictionary.md) are accepted;
in particular, stale timeout must exceed online timeout. It appends
`setting.updated` and returns `{ "setting": ... }`. Unknown keys/invalid values
return the standard 422 envelope.

## Live WebSocket protocol

The browser connects to `/api/v1/ws/live` with the same valid session cookie,
then sends a typed subscription message. It may send another valid subscription
to replace its current filters:

```json
{
  "type": "subscribe",
  "device_ids": [],
  "event_types": ["measurement.new", "alarm.changed", "device.status"]
}
```

An empty list means no restriction for that dimension. At most 200 device IDs
and five event types are accepted. Server messages always use:

```json
{
  "type": "measurement.new",
  "emitted_at": "2026-08-15T19:30:02Z",
  "sequence": 10482,
  "payload": {}
}
```

Event types are `subscription.confirmed`, `measurement.new`, `alarm.changed`,
`device.status`, and `heartbeat`. Events publish only after the database commit;
measurement events are coalesced to at most one per device/second and retain the
latest pending value. Heartbeats are sent every five seconds.

The browser shows `Reconnecting` after closure or five seconds without a
message, retries from one second with exponential backoff capped at 30 seconds,
and refetches REST after reconnect or a sequence gap. WebSocket payloads are
notifications, not the permanent state or historical record.

## Health/readiness

`GET /health` proves only that the API process can answer and returns service
name/version. `GET /ready` additionally requires PostgreSQL connectivity and
the schema revision to equal the single Alembic head, currently `0003`. Neither
endpoint returns configuration or credentials. Orchestration must use
readiness—not liveness—as the migration/database acceptance signal.
