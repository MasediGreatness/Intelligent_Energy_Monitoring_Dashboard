#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
compose_file="${COMPOSE_FILE:-${repo_root}/infra/docker-compose.pi.yml}"
env_file="${ENV_FILE:-${repo_root}/infra/.env.pi}"

usage() {
  cat <<'EOF'
Usage: ENV_FILE=infra/.env.pi ./infra/scripts/prepare-demo.sh [MODE]

Prepare the deterministic Step 16 demonstration in an already migrated,
otherwise empty database. The script refuses to delete or overwrite existing
measurements, forecasts, anomalies, or alarms.

Modes:
  --prepare        Fresh normal/peak/anomaly seed (default)
  --power-quality Stage a current low-power-factor snapshot
  --dropout        Stage a 120-second device-dropout window
  --manifest       Print current fixture provenance and integrity counts

Optional environment variables:
  COMPOSE_FILE  Compose file (default: infra/docker-compose.pi.yml)
  ENV_FILE      Compose environment file (default: infra/.env.pi)
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
mode="${1:---prepare}"
if [[ $# -gt 1 ]] || [[ ! "${mode}" =~ ^--(prepare|power-quality|dropout|manifest)$ ]]; then
  usage >&2
  exit 2
fi

for required in "${compose_file}" "${env_file}"; do
  if [[ ! -f "${required}" ]]; then
    echo "Required file not found: ${required}" >&2
    exit 1
  fi
done
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required." >&2
  exit 1
fi

compose=(docker compose --env-file "${env_file}" -f "${compose_file}")

for service in db api; do
  container_id="$("${compose[@]}" ps -q "${service}")"
  if [[ -z "${container_id}" ]]; then
    echo "Service '${service}' is not running. Start the migrated stack first." >&2
    exit 1
  fi
done

print_manifest() {
  "${compose[@]}" exec -T db psql -U energy -d energy -P pager=off -c "
  WITH totals AS (
    SELECT measured_at, sum(active_power_kw) AS total_kw
    FROM measurements
    WHERE active_power_kw IS NOT NULL
    GROUP BY measured_at
  )
  SELECT
    (SELECT count(*) FROM devices) AS devices,
    (SELECT count(*) FROM measurements) AS measurements,
    (SELECT count(*) FROM forecasts) AS forecasts,
    (SELECT count(*) FROM anomalies) AS anomalies,
    (SELECT count(*) FROM alarms) AS alarms,
    (SELECT round(max(total_kw)::numeric, 3) FROM totals) AS overall_maximum_combined_kw,
    (SELECT round(((value_json #>> '{}')::numeric * 1.05), 3)
       FROM settings WHERE key='demand_limit_kw') AS demo_peak_combined_kw,
    (SELECT value_json #>> '{}' FROM settings WHERE key='demand_limit_kw') AS limit_kw,
    (SELECT round(min(power_factor)::numeric, 3)
       FROM measurements AS measurement
       JOIN devices AS device ON device.id = measurement.device_id
      WHERE device.code='LOAD-002') AS minimum_conveyor_power_factor,
    (SELECT count(*) FROM (
       SELECT device_id, measured_at FROM measurements
       GROUP BY device_id, measured_at HAVING count(*) > 1
     ) AS duplicates) AS duplicate_groups;
  "
}

if [[ "${mode}" == "--manifest" ]]; then
  print_manifest
  exit 0
fi

if [[ "${mode}" == "--power-quality" ]]; then
  "${compose[@]}" exec -T api python - <<'PY'
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import Device, Measurement
from app.simulator.generator import Scenario, SimulationResult, generate_simulation
from app.simulator.persistence import persist_simulation

now = datetime.now(UTC).replace(microsecond=0)
generated = generate_simulation(
    now - timedelta(seconds=1), 3, get_settings().SIMULATOR_SEED,
    Scenario.LOW_POWER_FACTOR,
)
target = now
source_records = [item for item in generated.measurements if item.measured_at == target]
if len(source_records) != 5:
    raise SystemExit("Expected one deterministic midpoint record per device.")

with get_session_factory()() as session:
    identifiers = {
        code: device_id
        for code, device_id in session.execute(select(Device.code, Device.id))
    }
    staged = []
    for record in source_records:
        device_id = identifiers[record.device_code]
        latest = session.scalar(
            select(Measurement)
            .where(Measurement.device_id == device_id)
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        if latest is None or latest.energy_kwh_total is None:
            raise SystemExit("Run --prepare before --power-quality.")
        increment = Decimal(str(record.active_power_kw or 0)) / Decimal("3600")
        staged.append(
            record.model_copy(
                update={
                    "energy_kwh_total": (
                        latest.energy_kwh_total + increment
                    ).quantize(Decimal("0.000001"))
                }
            )
        )
    summary = persist_simulation(
        session, SimulationResult(tuple(staged), (), (), ())
    )
    for record in staged:
        session.scalar(select(Device).where(Device.code == record.device_code)).last_seen_at = target
    session.commit()
    conveyor = next(item for item in staged if item.device_code == "LOAD-002")
    print({**summary, "measured_at": target.isoformat(), "LOAD-002_power_factor": conveyor.power_factor})
PY
  print_manifest
  exit 0
fi

if [[ "${mode}" == "--dropout" ]]; then
  "${compose[@]}" exec -T api python - <<'PY'
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import Device, Measurement
from app.simulator.generator import Scenario, SimulationResult, generate_simulation
from app.simulator.persistence import persist_simulation

now = datetime.now(UTC).replace(microsecond=0)
start = now - timedelta(seconds=120)
generated = generate_simulation(
    start, 120, get_settings().SIMULATOR_SEED, Scenario.DEVICE_DROPOUT
)

with get_session_factory()() as session:
    latest_at = session.scalar(select(func.max(Measurement.measured_at)))
    if latest_at is None:
        raise SystemExit("Run --prepare before --dropout.")
    if latest_at >= start:
        wait = int((latest_at - start).total_seconds()) + 2
        raise SystemExit(
            f"Wait at least {wait} more seconds so the dropout window does not overlap existing data."
        )
    identifiers = {
        code: device_id
        for code, device_id in session.execute(select(Device.code, Device.id))
    }
    by_device = defaultdict(list)
    for record in generated.measurements:
        by_device[record.device_code].append(record)
    staged = []
    for device_code, records in by_device.items():
        device_id = identifiers[device_code]
        latest = session.scalar(
            select(Measurement)
            .where(Measurement.device_id == device_id)
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        if latest is None or latest.energy_kwh_total is None:
            raise SystemExit("Every seeded device must have a cumulative-energy baseline.")
        first = records[0]
        generated_baseline = first.energy_kwh_total
        if generated_baseline is None:
            raise SystemExit("The deterministic scenario must contain cumulative energy.")
        generated_baseline -= Decimal(str(first.active_power_kw or 0)) / Decimal("3600")
        offset = latest.energy_kwh_total - generated_baseline
        for record in records:
            if record.energy_kwh_total is None:
                staged.append(record)
            else:
                staged.append(
                    record.model_copy(
                        update={
                            "energy_kwh_total": (
                                record.energy_kwh_total + offset
                            ).quantize(Decimal("0.000001"))
                        }
                    )
                )
    summary = persist_simulation(
        session,
        SimulationResult(tuple(staged), generated.forecasts, (), generated.events),
    )
    for device_code, records in by_device.items():
        session.scalar(select(Device).where(Device.code == device_code)).last_seen_at = records[-1].measured_at
    session.commit()
    print({**summary, "start": start.isoformat(), "end": (now - timedelta(seconds=1)).isoformat()})
PY
  print_manifest
  exit 0
fi

existing="$("${compose[@]}" exec -T db psql -U energy -d energy -Atqc \
  "SELECT (SELECT count(*) FROM measurements),
          (SELECT count(*) FROM forecasts),
          (SELECT count(*) FROM anomalies),
          (SELECT count(*) FROM alarms);")"
IFS='|' read -r measurement_count forecast_count anomaly_count alarm_count <<<"${existing}"
if (( measurement_count != 0 || forecast_count != 0 || anomaly_count != 0 || alarm_count != 0 )); then
  cat >&2 <<EOF
Refusing to prepare the demonstration because scenario data already exists:
  measurements=${measurement_count}, forecasts=${forecast_count}, anomalies=${anomaly_count}, alarms=${alarm_count}
Use a fresh demo project/volume. This script never deletes existing records.
EOF
  exit 1
fi

now_epoch="$(date -u +%s)"
iso_at() {
  date -u -d "@$1" +'%Y-%m-%dT%H:%M:%SZ'
}

# Four adjacent deterministic windows end one second before preparation time.
# They are recent enough for dashboard charts while retaining clear provenance.
normal_start="$(iso_at "$((now_epoch - 600))")"
peak_start="$(iso_at "$((now_epoch - 420))")"
peak_end="$(iso_at "$((now_epoch - 240))")"
anomaly_start="$(iso_at "$((now_epoch - 240))")"

"${compose[@]}" exec -T api python -m app.simulator.cli seed
"${compose[@]}" exec -T \
  -e NORMAL_START="${normal_start}" \
  -e PEAK_START="${peak_start}" \
  -e ANOMALY_START="${anomaly_start}" \
  api python - <<'PY'
import os
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import Device, Measurement
from app.simulator.generator import Scenario, SimulationResult, generate_simulation
from app.simulator.persistence import persist_simulation


def parse_time(name: str) -> datetime:
    return datetime.fromisoformat(os.environ[name].replace("Z", "+00:00"))


def stage(session, start: datetime, seconds: int, scenario: Scenario) -> None:
    generated = generate_simulation(
        start, seconds, get_settings().SIMULATOR_SEED, scenario
    )
    identifiers = {
        code: device_id
        for code, device_id in session.execute(select(Device.code, Device.id))
    }
    by_device = defaultdict(list)
    for record in generated.measurements:
        by_device[record.device_code].append(record)
    staged = []
    for device_code, records in by_device.items():
        device_id = identifiers[device_code]
        latest = session.scalar(
            select(Measurement)
            .where(Measurement.device_id == device_id)
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        if latest is None or latest.energy_kwh_total is None:
            staged.extend(records)
            continue
        first = records[0]
        first_increment = Decimal(str(first.active_power_kw or 0)) / Decimal("3600")
        generated_baseline = first.energy_kwh_total - first_increment
        offset = latest.energy_kwh_total - generated_baseline
        staged.extend(
            record.model_copy(
                update={
                    "energy_kwh_total": (
                        record.energy_kwh_total + offset
                    ).quantize(Decimal("0.000001"))
                }
            )
            for record in records
            if record.energy_kwh_total is not None
        )
    summary = persist_simulation(
        session,
        SimulationResult(
            tuple(staged), generated.forecasts, generated.anomalies, generated.events
        ),
    )
    for device_code, records in by_device.items():
        session.scalar(
            select(Device).where(Device.code == device_code)
        ).last_seen_at = records[-1].measured_at
    session.commit()
    print({"scenario": scenario.value, **summary})


with get_session_factory()() as database_session:
    stage(database_session, parse_time("NORMAL_START"), 180, Scenario.NORMAL)
    stage(database_session, parse_time("PEAK_START"), 180, Scenario.PEAK_DEMAND)
    stage(
        database_session,
        parse_time("ANOMALY_START"),
        120,
        Scenario.SUDDEN_OVERCONSUMPTION,
    )
PY

"${compose[@]}" exec -T db psql -v ON_ERROR_STOP=1 -U energy -d energy -c "
UPDATE devices AS device
SET last_seen_at = latest.measured_at
FROM (
  SELECT device_id, max(measured_at) AS measured_at
  FROM measurements GROUP BY device_id
) AS latest
WHERE latest.device_id = device.id;
"

# The simulator deliberately owns measurement/forecast/anomaly data only. These
# two alarm rows are deterministic demonstration fixtures. Each is derived from
# the stored combined peak series and the configured limit; neither claims to
# be output from a production alarm-evaluation service.
"${compose[@]}" exec -T db psql -v ON_ERROR_STOP=1 -U energy -d energy \
  -v peak_start="${peak_start}" -v peak_end="${peak_end}" <<'SQL'
BEGIN;

WITH peak_totals AS (
  SELECT measured_at, sum(active_power_kw) AS total_kw
  FROM measurements
  WHERE measured_at >= :'peak_start'::timestamptz
    AND measured_at < :'peak_end'::timestamptz
    AND active_power_kw IS NOT NULL
  GROUP BY measured_at
), derived_limit AS (
  SELECT round((max(total_kw)::numeric / 1.05), 3)::double precision AS value
  FROM peak_totals
)
UPDATE settings AS setting
SET value_json = to_jsonb(derived_limit.value), updated_at = now()
FROM derived_limit
WHERE setting.key = 'demand_limit_kw';

WITH limit_value AS (
  SELECT (value_json #>> '{}')::double precision AS demand_limit_kw
  FROM settings WHERE key = 'demand_limit_kw'
), peak_totals AS (
  SELECT measured_at, sum(active_power_kw) AS total_kw
  FROM measurements
  WHERE measured_at >= :'peak_start'::timestamptz
    AND measured_at < :'peak_end'::timestamptz
    AND active_power_kw IS NOT NULL
  GROUP BY measured_at
), warning_crossing AS (
  SELECT measured_at, total_kw, demand_limit_kw
  FROM peak_totals CROSS JOIN limit_value
  WHERE total_kw >= demand_limit_kw * 0.90
  ORDER BY measured_at
  LIMIT 1
)
INSERT INTO alarms (
  id, device_id, source, alarm_type, severity, message, triggered_at, status
)
SELECT
  '00000000-0000-4000-8000-000000000901'::uuid,
  NULL,
  'deterministic_demo_fixture',
  'demand_warning',
  'medium',
  'Simulated combined demand ' || round(total_kw::numeric, 3) ||
    ' kW crossed 90% of the configured ' ||
    round(demand_limit_kw::numeric, 3) || ' kW limit.',
  measured_at,
  'open'
FROM warning_crossing;

WITH limit_value AS (
  SELECT (value_json #>> '{}')::double precision AS demand_limit_kw
  FROM settings WHERE key = 'demand_limit_kw'
), peak_totals AS (
  SELECT measured_at, sum(active_power_kw) AS total_kw
  FROM measurements
  WHERE measured_at >= :'peak_start'::timestamptz
    AND measured_at < :'peak_end'::timestamptz
    AND active_power_kw IS NOT NULL
  GROUP BY measured_at
), high_crossing AS (
  SELECT measured_at, total_kw, demand_limit_kw
  FROM peak_totals CROSS JOIN limit_value
  WHERE total_kw >= demand_limit_kw
  ORDER BY measured_at
  LIMIT 1
)
INSERT INTO alarms (
  id, device_id, source, alarm_type, severity, message, triggered_at, status
)
SELECT
  '00000000-0000-4000-8000-000000000902'::uuid,
  NULL,
  'deterministic_demo_fixture',
  'demand_high',
  'high',
  'Simulated combined demand ' || round(total_kw::numeric, 3) ||
    ' kW crossed the configured ' ||
    round(demand_limit_kw::numeric, 3) || ' kW limit.',
  measured_at,
  'open'
FROM high_crossing;

COMMIT;
SQL

echo
echo "DEMO_PREPARED"
print_manifest

cat <<EOF
Scenario windows (UTC):
  normal:               ${normal_start} for 180 seconds
  peak_demand:          ${peak_start} for 180 seconds
  sudden_overconsumption: ${anomaly_start} for 120 seconds

Next: follow docs/demo.md. Power quality, dropout, and API restart are staged
during the presentation so the visible transitions use current timestamps.
EOF
