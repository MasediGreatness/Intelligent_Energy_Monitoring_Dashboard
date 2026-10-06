# Step 16 demonstration guide

## Purpose and safety boundary

This is the reproducible 7-10 minute demonstration for the monitoring-only
dashboard. It uses deterministic simulator seed `118`; it does not use real
sensor, gateway, machine-learning, relay, contactor, load-shedding, or
load-restoration output. Every scenario and alarm shown during the demonstration
must be described as simulated.

Use a dedicated empty demonstration database. `prepare-demo.sh` refuses to run
when measurements, forecasts, anomalies, or alarms already exist and never
deletes data. Do not reset the only production volume for a demonstration.

The Raspberry Pi hardware acceptance, reboot, restore, and physical
power-interruption checks are separate and remain pending until the signed
[Step 15 hardware checklist](test-evidence/step-15-pi-hardware-checklist.md)
is completed.

## One-time preparation

Complete the deployment and migration sections in [operations.md](operations.md).
For an assessed rehearsal, create a separate Compose project from the protected
Pi environment file:

```bash
install -m 600 infra/.env.pi /tmp/intelligent-energy-demo.env
sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=intelligent-energy-demo/' \
  /tmp/intelligent-energy-demo.env
sed -i 's/^DASHBOARD_PORT=.*/DASHBOARD_PORT=18081/' \
  /tmp/intelligent-energy-demo.env

compose=(docker compose --env-file /tmp/intelligent-energy-demo.env \
  -f infra/docker-compose.pi.yml)
"${compose[@]}" up -d db
"${compose[@]}" run --rm migrate
"${compose[@]}" up -d api web
```

Create the demonstration administrator interactively. Do not put its password
in the repository, shell history, screenshots, or evidence log:

```bash
"${compose[@]}" exec api python -m app.cli.create_user \
  --email YOUR_VALID_EMAIL --role admin
```

Prepare the normal, peak, anomaly, forecast, and alarm fixtures:

```bash
ENV_FILE=/tmp/intelligent-energy-demo.env \
  ./infra/scripts/prepare-demo.sh --prepare | tee /tmp/step-16-demo-prepare.txt
```

The preparation output must report five devices, 2,400 measurements, 15
forecasts, one anomaly, two open alarms, and zero duplicate groups. It reports
the overall maximum separately from `demo_peak_combined_kw`, because the
single-device anomaly can make the overall maximum larger than the scripted
peak-window maximum. The demand limit is always calculated as
`demo_peak_combined_kw / 1.05`, so the scripted peak reaches 105% of the
configured limit. The normal profile remains below 90% because the peak
multiplier is 1.22.

Open `http://PI_PRIVATE_IP:18081/login`, sign in, and keep a terminal in the
repository root. For a first installation using the primary empty stack, use
`infra/.env.pi` and its configured port instead.

## Timed demonstration

The timings are a speaking guide, not a performance claim. Pause briefly after
navigation or a refresh so the audience can see loading and authoritative API
state.

| Time | Action | Expected, traceable observation |
|---:|---|---|
| 0:00-0:45 | State scope and sign in. | The system is monitoring/advisory only. The user menu identifies the authenticated role; no control action exists. |
| 0:45-1:45 | Open **History**, set both dates to today and interval to `10s`. | The first three-minute block is the stable `normal` profile. Five device series come from stored one-second simulator measurements aggregated into ten-second means. |
| 1:45-2:45 | Continue along the same chart into the next three-minute block, then open **Overview**. | The peak block rises by the documented 1.22 multiplier. Recent alarms show 90% warning and 100% high crossings derived from the stored combined series and the displayed threshold. |
| 2:45-3:45 | Open **Forecast and anomalies**. | The single compressor anomaly shows expected value, actual value, score `0.91`, severity, and the explanation that actual demand is 35% above the expected profile. Forecasts are labelled `simulator-v1-seed-118`, not trained ML output. |
| 3:45-4:30 | Run the power-quality command below, immediately open **Live**, and refresh once. | `LOAD-002` shows power factor near `0.72`. The script output records the exact value. If it ages beyond the status timeout, the UI labels it stale/offline rather than presenting it as live. |
| 4:30-5:45 | Explain data-quality states and allow at least 125 seconds after the power-quality command. Then run the dropout command below and refresh **Live**. | `LOAD-003` stopped producing halfway through the 120-second window, so it is offline; the other four devices have recent samples. Historical energy is retained and the pump is excluded from current demand rather than replaced with zero. |
| 5:45-6:45 | Open **Alarms**, inspect one open fixture, enter a non-empty review note, and acknowledge it. | Status becomes `acknowledged`; the authenticated user ID, UTC time, note, and immutable `alarm.acknowledged` event are stored. |
| 6:45-7:45 | With **Live** open, restart only the API using the command below. | The connection badge changes to `Reconnecting`; after health returns it changes to `Connected`, detects recovery, and refetches authoritative REST state. No page reload or fabricated zero is required. |
| 7:45-9:00 | Print the manifest, show Settings, then summarise limitations. | Counts, maximum demand, limit, minimum conveyor power factor, and duplicate groups are independently queryable. Settings show the fixed timezone, timeouts, demand interval, tariff, and simulator profile. Physical Pi and future gateway/ML integration are not claimed complete. |

### Power-quality transition

Run this while the audience can see the terminal, then refresh Live promptly:

```bash
ENV_FILE=/tmp/intelligent-energy-demo.env \
  ./infra/scripts/prepare-demo.sh --power-quality
```

This mode takes the deterministic middle sample of the low-power-factor
scenario, preserves each device's cumulative-energy continuity, and stores one
current sample per device. It is presentation staging, not a production power-
quality detector.

### Communication dropout transition

Run this at least 125 seconds after the power-quality command. The guard aborts
instead of overlapping existing timestamps:

```bash
ENV_FILE=/tmp/intelligent-energy-demo.env \
  ./infra/scripts/prepare-demo.sh --dropout
```

The pump (`LOAD-003`) emits only the first half of the window. Its last sample
is then older than the configured 60-second stale timeout. The script offsets
the generated cumulative counters onto the existing counters so the staged
transition does not invent a meter reset.

### API/WebSocket recovery

```bash
"${compose[@]}" restart api
"${compose[@]}" ps
curl --fail --silent "http://PI_PRIVATE_IP:18081/ready"
```

Keep the browser on Live while the restart runs. The WebSocket is only a
notification path: the browser refetches REST after reconnection, and
PostgreSQL remains authoritative.

### Final manifest

```bash
ENV_FILE=/tmp/intelligent-energy-demo.env \
  ./infra/scripts/prepare-demo.sh --manifest | tee /tmp/step-16-demo-final.txt
```

Expected integrity conditions are five devices, one anomaly, two alarms before
acknowledgement, at least 15 forecasts, and zero duplicate
`(device_id, measured_at)` groups. Retain the two `/tmp/step-16-demo-*.txt`
files with the assessed evidence only after checking that they contain no
credentials.

## Displayed-value provenance

| Displayed value | Authoritative source | Documented rule |
|---|---|---|
| Current demand | Latest stored measurement per enabled device, returned by `GET /api/v1/dashboard/summary` | Sum `active_power_kw` only for non-missing samples no older than `stale_timeout_seconds`; report exclusions. |
| Current-demand comparison | Same summary endpoint | Compare current demand with the latest eligible values at exactly 15 minutes earlier; `(current - prior) / prior * 100`; null when prior is zero or missing. |
| Energy today | Cumulative `energy_kwh_total` measurements | Sum positive counter deltas since local midnight, split at resets, and report missing baseline rather than inventing energy. |
| Peak demand | Stored measurements and configured demand interval | Maximum time-weighted interval with at least 90% completeness; otherwise `-`. |
| Demand threshold | `settings.demand_limit_kw` | Demonstration preparation sets `round(max peak combined kW / 1.05, 3)` so the scripted peak crosses the configured limit. |
| Active-alarm counts | Non-cleared rows in `alarms` | Group by severity. Acknowledged remains active until cleared. |
| Device online/stale/offline | Latest measurement time plus settings | Online age `<= 10s`; stale `>10s` and `<=60s`; offline absent or `>60s`; disabled is separate. |
| Completeness and gaps | Expected one-second sample grid versus valid stored timestamps | `valid / expected * 100`; missing values are not interpolated and are never converted to zero. |
| History chart and CSV | `GET /api/v1/measurements/history` | Backend-owned raw or fixed bucket mean, sample count, and completeness. CSV preserves UTC timestamps, units, and blanks. |
| Latest voltage/current/kW/PF/frequency | Latest row from `measurements` | Values are simulator electrical outputs with fixed SI units; null displays `-`. |
| Ten-second normal/peak series | Seed `118` measurement rows | Base device/time profile with deterministic hash noise; peak uses `1.22` during the middle 40% of its window. |
| Power-quality value | Staged deterministic midpoint for `LOAD-002` | Scenario sets PF to `0.72 + deterministic noise` during the active window; all other electrical fields come from the same record. |
| Forecast, confidence band, version | Latest `forecasts` rows | Prediction is latest combined demand times `1 + 0.015*sin(horizon/4)`; lower/upper are 94%/106%; version is `simulator-v1-seed-118`. |
| Anomaly expected/actual/score | Deterministic `anomalies` row | Compressor expected value is its time profile; actual is `expected * 1.35`; score is the fixed simulator fixture `0.91`. |
| Warning/high alarms | Rows sourced `deterministic_demo_fixture` | First combined peak timestamp `>= 90%` of limit creates medium warning; first `>= 100%` creates high alarm. These are fixture records, not output from an implemented rule engine. |
| Acknowledgement attribution | Alarm row plus `system_events` | Operator/admin only; record current user ID, UTC time, required note, and append-only audit event. |
| WebSocket state | Authenticated live connection and heartbeat | Show reconnecting after heartbeat loss; exponential retry capped at 30 seconds; sequence gap/recovery triggers REST refetch. |

The implementation locations, tests, and evidence for these rules are mapped in
[final-requirements-traceability.md](final-requirements-traceability.md).

## Known limitations to say aloud

- Peak alarms in this demonstration are deterministic fixture rows calculated
  from stored measurements. A continuous production alarm-rule evaluator is a
  future integration item.
- Forecasts and anomaly records are deterministic contract fixtures, not trained
  model results or claims of predictive accuracy.
- Simulator persistence is a development/demo source. The future gateway must
  call the authenticated public ingestion contract and provide calibrated data.
- The dashboard does not and must not control industrial loads.
- Billing-grade accuracy, sensor calibration, public cloud exposure, and
  production certification are out of scope.
- ARM64 cross-build and local recovery evidence exist, but real Raspberry Pi
  clean-install, reboot, restore, and physical power-loss evidence remains
  pending until the Step 15 checklist is completed.

## Rehearsal record

Copy this block into the Step 16 evidence after each assessed run:

```text
Date/time (UTC):
Presenter/reviewer:
Git commit or immutable image tag:
Host/Pi model and OS:
Start/end time and duration:
Prepare manifest filename:
Final manifest filename:
Normal / peak / anomaly / power quality / dropout: PASS | FAIL
Acknowledgement actor, note and event checked: PASS | FAIL
Reconnect -> REST recovery checked: PASS | FAIL
Duplicate groups = 0: PASS | FAIL
Physical Pi Step 15 checklist: PENDING | PASS (evidence path)
Defects/observations:
Reviewer signature/date:
```

Do not mark the Step 16 gate complete merely because the script ran. The
student must personally reproduce the flow and explain the source, formula,
test, assumption, and limitation for each item in the sign-off checklist.
