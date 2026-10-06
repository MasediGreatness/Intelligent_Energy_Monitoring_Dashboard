# System Requirements

## Purpose and authority

These requirements translate the controlling *Intelligent Energy Dashboard Backend Codex Build Plan*, version 1.0 dated 15 August 2026, into traceable implementation statements. The PDF remains authoritative if wording here is ambiguous. Changes to a fixed contract require an approved ADR before implementation.

## Functional requirements

- **FR-001 — Dashboard overview.** The system shall present current demand, energy today, 15-minute peak demand, active alarms, a 24-hour demand/forecast/threshold chart, recent alarms, device-health counts, and last-update time.
- **FR-002 — Live monitoring.** The system shall present each device's latest voltage, current, active power, power factor, frequency, connection quality, and a 60-minute trend.
- **FR-003 — Energy history.** The system shall support date, device, and interval filters; power history; daily energy; 15-minute demand; equal-period comparison; and CSV export.
- **FR-004 — Forecasts and anomalies.** The system shall present actual versus predicted demand, a confidence band, model version, and anomaly type, metric, expected value, actual value, score, severity, status, and explanation.
- **FR-005 — Alarm lifecycle.** The system shall provide a filterable, paginated alarm view with open, acknowledged, and cleared states, details, and authorised acknowledgement with user, time, and note.
- **FR-006 — Device management.** The system shall show device identity, location, type/phase, criticality, rated power, last seen, enabled state, status, and data quality; admins may create or update devices, and records shall be disabled rather than hard-deleted.
- **FR-007 — Settings.** The system shall expose demand limit, demand interval, flat tariff and ZAR currency, timezone, online/stale timeouts, and simulator profile; only admins may edit them.
- **FR-008 — Simulator.** Development and demo profiles shall use a deterministic simulator with at least compressor, conveyor motor, pump, heater, and lighting devices and selectable normal, peak-demand, low-power-factor, sudden-overconsumption, device-dropout, and meter-reset scenarios.
- **FR-009 — Future-source compatibility.** The same public ingestion contract used by the simulator shall accept a future Raspberry Pi gateway without a dashboard rewrite and without simulator-only public measurement fields.
- **FR-010 — Measurement ingestion.** `POST /api/v1/ingest/measurements` shall authenticate with `X-Ingest-Key`, accept bounded batches, validate each record, write valid records efficiently, report accepted/duplicate/rejected counts and per-record errors, and reject a whole batch only for invalid authentication or malformed JSON.
- **FR-011 — Idempotency.** A measurement shall be unique by `(device_id, measured_at)`; a duplicate shall be reported as accepted-but-duplicate and shall not create another row.
- **FR-012 — Measurement fields.** The public measurement contract shall use `device_code`, `measured_at`, `voltage_v`, `current_a`, `active_power_kw`, `reactive_power_kvar`, `apparent_power_kva`, `power_factor`, `frequency_hz`, `energy_kwh_total`, and `data_quality` with the units and meanings fixed by the specification.
- **FR-013 — Measurement validation.** The backend shall enforce the documented timestamp, voltage, current, active-power, power-factor, frequency, cumulative-energy, reset, and data-quality rules and return field-level validation information.
- **FR-014 — Device status.** Online means latest-record age at most `online_timeout_seconds`; stale means older than online timeout and at most `stale_timeout_seconds`; offline means no record or older than stale timeout; disabled is reported separately.
- **FR-015 — Current demand.** Current demand shall sum only the latest `active_power_kw` for enabled, non-stale devices and shall report excluded-device count.
- **FR-016 — Energy today.** Per-device energy shall be derived from valid cumulative-meter segments relative to local midnight, identify baseline gaps, and split at resets instead of subtracting across them.
- **FR-017 — Demand and peak.** Demand shall be the time-weighted mean active power over the configured interval (15 minutes by default), and peak demand shall be the maximum valid interval demand in the selected local day.
- **FR-018 — Previous-period comparison.** Comparisons shall use equal elapsed periods, such as today 00:00–14:00 versus yesterday 00:00–14:00.
- **FR-019 — Estimated cost.** Estimated cost shall equal valid energy in kWh multiplied by the configured flat tariff, be labelled as an estimate, and use ZAR.
- **FR-020 — Completeness.** The backend shall return expected samples, valid samples, percentage completeness, and gaps without silently interpolating missing values.
- **FR-021 — Aggregation.** Measurement queries shall support `raw`, `10s`, `1m`, `15m`, `1h`, and `1d` buckets with bucket timestamps, sample counts, and completeness.
- **FR-022 — Data persistence.** PostgreSQL shall store users, devices, measurements, forecasts, anomalies, alarms, immutable system events, and settings with the minimum fields, relationships, constraints, and indexes specified in Sections 4.2 and 4.3.
- **FR-023 — Authentication.** The API shall provide `/api/v1/auth/login`, `/logout`, and `/me`, securely hash passwords, expire credentials, rate-limit login, and create users only through explicit setup using non-committed credentials.
- **FR-024 — Roles.** Viewers, operators, and admins may view and export; operators and admins may acknowledge alarms; only admins may edit devices/settings; no role may issue a real load-control command.
- **FR-025 — Audit events.** Login failures, alarm acknowledgements, settings/device changes, and relevant ingestion/system events shall be recorded without storing passwords or tokens.
- **FR-026 — Health and readiness.** `GET /health` shall report process health without a database dependency; `GET /ready` shall clearly and safely report database connectivity and migration readiness.
- **FR-027 — Read APIs.** Under `/api/v1`, the backend shall implement the fixed summary, latest measurement, history, daily energy, forecast, anomaly, alarm, device, setting, and event endpoint inventory.
- **FR-028 — Query controls.** History, daily-energy, alarm, and anomaly endpoints shall support the documented parameters; history shall be limited to 31 days, raw history to 24 hours, and page size to 200.
- **FR-029 — API shapes.** Lists shall return `page`, `page_size`, `total`, and `items`; failures shall use the standard error envelope; dashboard summary shall follow the fixed response meaning; main success and error responses shall include OpenAPI examples.
- **FR-030 — Live protocol.** Authenticated `/api/v1/ws/live` shall accept device/event subscriptions and emit `measurement.new`, `alarm.changed`, `device.status`, and heartbeat messages containing `type`, `emitted_at`, `sequence`, and `payload`.
- **FR-031 — Live recovery.** Browser events shall be coalesced to at most one per device per second; the client shall show Reconnecting after five seconds without heartbeat, retry with exponential backoff capped at 30 seconds, detect sequence gaps, and refetch authoritative REST state after recovery.
- **FR-032 — UI information states.** Every data panel shall explicitly handle loading, empty, error, stale, and partial-data states; missing data shall display `-`, never a fabricated zero.
- **FR-033 — Navigation and responsive shell.** The UI shall provide routable Overview, Live, History, Forecast and Anomalies, Alarms, Devices, and Settings pages with desktop, tablet, and 375 px mobile behaviour defined in the specification.
- **FR-034 — Visual system.** The UI shall use the fixed colour palette, status semantics, units/precision, timestamp conventions, chart rules, feedback patterns, and reusable component inventory from Section 3.
- **FR-035 — Accessibility.** Core workflows shall support keyboard navigation, visible focus, semantic labels and headers, WCAG AA contrast, and reduced-motion preferences.
- **FR-036 — Configuration.** The application shall consume the environment variables listed in Section 6.2 with typed startup validation and shall not hard-code deployment URLs, device IDs, passwords, or secrets.
- **FR-037 — Database lifecycle.** Alembic shall version the schema from a clean database, support tested downgrade, and reject duplicate measurements and invalid enum values through database constraints.
- **FR-038 — Deployment.** Docker Compose shall provide PostgreSQL, API, web, and optional Nginx services using ARM64-compatible images, health checks, restart policies, a named database volume, and bounded logs.
- **FR-039 — Operations.** Documentation shall cover initial setup, migrations, admin creation, seed, backup, restore, upgrade, rollback, LAN-only binding, reboot recovery, and power-interruption behaviour.
- **FR-040 — Demonstration.** A fresh deterministic seed shall reproduce normal, peak, abnormal, power-quality, communication-dropout, acknowledgement, and API/WebSocket recovery scenarios in a 7–10 minute demonstration.
- **FR-041 — Evidence and handoff.** The repository shall retain architecture, data dictionary, API contract, ADRs, requirements traceability, OpenAPI, tests/results, simulator seed/scenario, performance evidence, screenshots, defect/retest records, limitations, and an AI Use Declaration.

## Non-functional requirements

- **NFR-001 — Fixed architecture.** The frontend shall access data only through versioned backend APIs; routes remain thin; services own business calculations; repositories own database access; ingestion writes and query services read/aggregate.
- **NFR-002 — Authoritative state.** PostgreSQL and REST shall be authoritative for stored/history state; WebSocket messages provide near-real-time updates and recovery notification only.
- **NFR-003 — Time.** Every stored timestamp shall be timezone-aware `TIMESTAMPTZ`, serialized as ISO 8601 UTC; the UI shall display Africa/Johannesburg by default with absolute tooltips and relative last-seen labels.
- **NFR-004 — Units and numeric types.** Field names shall include SI units; sampled electrical values shall use double precision; cumulative energy and tariff shall use decimal/numeric types; UI precision shall follow Section 3.3.
- **NFR-005 — Missing data honesty.** `NULL` plus explicit data quality shall represent missing measurements; zero shall retain its mathematical meaning.
- **NFR-006 — Performance.** Typical simulator-to-visible-update latency shall be at most two seconds on the LAN; 24 hours at one-minute resolution shall respond within two seconds on the Pi or documented equivalent; a 60-record batch shall meet a locally recorded target.
- **NFR-007 — Security.** Passwords shall use Argon2 or bcrypt; sessions shall use HttpOnly SameSite cookies or a documented short-lived access/refresh design; write routes shall enforce roles; ingestion/login shall be rate-limited; secrets shall not be committed or logged.
- **NFR-008 — Safety.** The MVP shall be monitoring and advisory only and shall never energise or expose an enabled Start, Stop, Shed, Restore, relay, contactor, or industrial-load command path.
- **NFR-009 — Reliability.** API, WebSocket, and database interruptions shall be visible to the user and recovery shall not corrupt data or create duplicate measurements.
- **NFR-010 — Test isolation.** Automated tests shall use an isolated test database and shall never use development or production data.
- **NFR-011 — Quality gates.** Python shall pass Ruff, static type checking, and Pytest; TypeScript shall pass ESLint, Prettier, Vitest/React Testing Library, and Playwright; CI shall fail on lint or test failure.
- **NFR-012 — Coverage.** Backend service/calculation coverage shall be at least 80%, with critical formulas and permission paths fully covered.
- **NFR-013 — Structured diagnostics.** The backend shall emit structured logs with request IDs and central error handling without exposing credentials.
- **NFR-014 — Reproducibility.** A clean checkout shall build, migrate, seed, test, and run using documented commands without manual source edits.
- **NFR-015 — Maintainability.** API types shall be generated from OpenAPI where practical or maintained in one central typed client; response shapes and calculation formulas shall not be duplicated in page components.
- **NFR-016 — Architecture governance.** Each architectural or fixed-contract change shall have an approved ADR describing context, options, decision, and consequences before implementation.
- **NFR-017 — Compatibility.** Core functions shall remain usable on desktop, tablet, and a 375 px mobile viewport, with horizontal scrolling restricted to intentional table containers.
- **NFR-018 — Raspberry Pi operation.** A clean Raspberry Pi 4 ARM64 deployment shall start from documented commands, survive reboot, restore a backup into a clean volume, and preserve documented measurement integrity after power interruption.
- **NFR-019 — Safe exposure.** Deployment shall be LAN-only by default; PostgreSQL and internal API surfaces shall not be directly exposed to the public internet.
- **NFR-020 — Academic ownership.** AI shall remain supportive; the student shall validate and be able to explain the code, designs, formulas, tests, choices, and limitations and shall provide the required signed/dated declaration.

## Explicitly out of scope

- **OOS-001:** Cortex-M4 firmware, sensing electronics, Modbus/RS-485 drivers, and calibration.
- **OOS-002:** Training forecasting or anomaly-detection models; the system only consumes fixed forecast/anomaly contracts populated by a simulator or later service.
- **OOS-003:** Real relay, contactor, load-shedding, load-restoration, or other industrial-load commands and control screens.
- **OOS-004:** Cloud hosting and public-internet exposure.
- **OOS-005:** Billing-grade metering and production certification.
