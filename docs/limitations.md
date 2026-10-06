# Known Limitations and Remaining Integration Work

## Purpose

This record prevents prototype evidence from being presented as field or
production certification. It distinguishes an implemented, locally tested
dashboard from hardware, model, security, and operational work that remains.

## Verification boundary

### Raspberry Pi acceptance is pending

Actual ARM64 target images, local production Compose, clean-volume restore,
abrupt PostgreSQL termination, and host restart were exercised successfully.
They do not substitute for the controlling Step 15 gate on a physical
Raspberry Pi 4. The following remain unverified until the student executes and
signs the [Pi checklist](test-evidence/step-15-pi-hardware-checklist.md):

- clean installation on the intended Pi/OS/storage;
- service recovery after a real Pi reboot;
- clean-volume restore with records visible in the Pi-hosted dashboard;
- integrity after a controlled physical power interruption;
- target-device response times, CPU, RAM, storage, and thermal observations;
- LAN scan confirming only the intended web port is reachable.

The repository must not claim Raspberry Pi deployment acceptance before those
checks pass.

### Test scope is prototype scope

Backend/unit/integration, frontend component, Chromium Playwright, packaging,
backup/restore, and local failure tests provide strong regression evidence. They
are not a formal safety assessment, penetration test, metering certification,
browser certification, long-duration soak test, or independent validation.
Accessibility checks cover automated rules and tested keyboard/responsive flows;
they are not a full assistive-technology audit.

## Data-source and engineering limitations

### Simulator, not measured plant data

The implemented source is deterministic synthetic data. Its scenarios are
designed to exercise contracts and UI states; they do not establish sensor
accuracy, plant load behaviour, energy savings, forecast accuracy, anomaly
detection performance, or generalisability. No voltage/current sensor,
calibration chain, Cortex-M4 firmware, Modbus/RS485 driver, or Pi gateway is
implemented.

The future gateway must:

1. emit the documented UTC/SI measurement contract;
2. authenticate with a separately provisioned ingest key;
3. preserve device codes and cumulative-counter/reset semantics;
4. retry idempotently with the original timestamps;
5. pass range, clock-skew, dropout, duplicate, performance, and recovery tests;
6. provide traceable calibration and uncertainty evidence outside this build.

### Forecasts and anomalies are placeholders

Simulator forecasts are labelled with a `simulator-*` model version. The
overconsumption anomaly is scripted through the future-compatible schema. No ML
model is trained, selected, calibrated, evaluated, deployed, or monitored.

Before real ML integration, define versioned feature/input contracts, training
and holdout datasets, baselines, error/coverage metrics, uncertainty semantics,
drift monitoring, missing-input behaviour, model rollback, and responsible-use
review. The UI must continue to show "model data unavailable" when no valid
output exists rather than inventing a prediction.

### Monitoring only; no load control

No role, route, database command, live event, simulator action, or UI control
can start, stop, shed, restore, or switch a real load. This is an intentional
safety boundary, not an unfinished dashboard button.

Any control integration requires a separate approved specification covering at
least hazard analysis, electrical protection, hardwired interlocks, fail-safe
states, manual override, command authority, strong authentication and replay
protection, supervision/feedback, audit, commissioning, emergency procedures,
and applicable regulatory/professional obligations.

## Calculation and interpretation limitations

- Energy derives from valid cumulative meter counters. Accuracy cannot exceed
  the producer/meter and timestamp quality.
- `good`/`suspect` quality is producer-supplied; this application does not
  independently calibrate or validate electrical instrumentation.
- A sample covers no more than one expected interval; gaps lower completeness.
  No silent interpolation is performed.
- Peak demand uses the accepted backend interval/completeness rule. It is not a
  tariff-authority billing demand unless separately validated against that
  tariff/meter definition.
- Estimated cost is only `valid kWh x flat ZAR/kWh`. It excludes time-of-use,
  demand, capacity, reactive-energy, tax, fixed, and negotiated charges.
- Negative active power is contractually reserved for export/generation, but no
  production generation workflow is validated.
- History is intentionally bounded to 31 days/request and raw data to 24 hours.
  The current schema is retention-ready but implements no automatic retention,
  partitioning, archival, or downsampling policy.

## Security and deployment limitations

### Private-LAN HTTP by default

The supplied Pi Nginx configuration serves HTTP and does not terminate TLS.
`SESSION_COOKIE_SECURE=false` is therefore required for the documented private
LAN HTTP profile; this protects the token from JavaScript via `HttpOnly` but
does **not** encrypt credentials, cookies, or data in transit. The system must
remain on a trusted, segmented private LAN and must not be port-forwarded or
exposed to the public internet.

For any less-trusted network, add tested HTTPS termination and certificate
lifecycle management, set `SESSION_COOKIE_SECURE=true`, retain SameSite and
HttpOnly protections, and repeat login/WebSocket/recovery tests through the TLS
endpoint. A VPN or authenticated reverse proxy requires its own threat review.

### Authentication is intentionally small-scope

- Users are provisioned/reset by a local explicit CLI; there is no self-service
  registration, password-reset email, MFA, SSO, or account-management UI.
- The ingest boundary uses one configured shared secret; automated rotation,
  per-device keys, mTLS, and revocation UI are not implemented.
- Sessions are opaque, revocable, and time-bounded, but there is no distributed
  session cache because the target is one API worker.
- Secret management uses untracked environment files. A production secret
  manager/HSM is outside scope.
- Security dependencies and base images require ongoing patching and rescans;
  passing current tests is not a permanent vulnerability guarantee.

### Single-node/single-worker design

The Pi, database volume, Nginx, and single FastAPI worker are one failure domain.
There is no high availability, replication, automatic failover, or zero-downtime
upgrade. The in-process WebSocket sequence/connection manager is valid only for
one API worker; horizontal scaling requires a shared broker and global sequence.

Backups are guarded and checksum-validated but operator-triggered. They provide
no resilience if stored only on the same Pi/storage. Establish off-device,
access-controlled retention and periodic restore drills for real operation.

### Operational observability

Structured logs, request IDs, health/readiness endpoints, audit events, and
bounded container logs are implemented. Central log retention, metrics,
alerting, uptime monitoring, time synchronisation monitoring, storage-health
monitoring, and incident response are not.

## UI and compatibility limitations

- End-to-end browser evidence uses Chromium. Other browser/OS combinations need
  explicit compatibility testing.
- The UI offers Johannesburg and UTC timezone choices even though the backend
  validates general IANA zones.
- Chart accuracy depends on returned bounded buckets; the browser deliberately
  enforces coarser aggregation for long ranges.
- The Vite production build reports an accepted low-severity main-bundle size
  warning. It is a performance-maintenance item, not a correctness failure.
- An API/WebSocket outage is shown honestly and recovered by refetch, but no
  offline application mode is implemented.

## Outstanding handoff decisions

| Area | Required next evidence/decision |
|---|---|
| Physical Pi | Complete and sign every Step 15 hardware check |
| Gateway | Hardware/interface specification, identity/key lifecycle, clock and calibration tests |
| ML | Dataset/model/evaluation/versioning/drift specification and honest unavailable state |
| Load control | Separate safety case and approved control architecture; never extend this MVP silently |
| TLS/remote access | Threat model, endpoint architecture, certificates, secure-cookie test, network controls |
| Data lifecycle | Retention, partitioning, archival, backup destination, restore frequency |
| Scaling | Shared live-event broker/global sequence and multi-worker tests if one worker is insufficient |
| Field acceptance | Long-duration run, power/network fault campaign, performance/thermal baseline, user evaluation |

## Academic claim boundary

The demonstration may show implementation and controlled prototype evidence.
It must clearly distinguish simulated from measured/modelled results and pending
from passed gates. The student remains responsible for reviewing the code and
evidence, explaining each formula and decision, performing the unsigned checks,
and making only claims supported by retained results.
