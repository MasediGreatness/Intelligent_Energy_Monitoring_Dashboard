# Deterministic Simulator

The development/demo simulator emits the same public measurement contract expected from the future Raspberry Pi gateway. It does not add `scenario`, `seed`, or other simulator-only measurement fields.

## Seeded devices

| Code | Load | Rated kW | Criticality |
|---|---|---:|---|
| LOAD-001 | Main Air Compressor | 18.5 | Critical |
| LOAD-002 | Line Conveyor Motor | 11.0 | High |
| LOAD-003 | Process Water Pump | 7.5 | High |
| LOAD-004 | Process Heater | 15.0 | Medium |
| LOAD-005 | Factory Lighting | 5.0 | Low |

Device IDs are stable UUIDv5 values derived from their codes. Running seed repeatedly updates these records rather than duplicating them.

## Scenarios

- `normal`: time-of-day load profiles, small deterministic electrical variation, and monotonic energy counters.
- `peak_demand`: all active loads rise during the middle 40 percent of the run.
- `low_power_factor`: the conveyor power factor falls to approximately 0.72.
- `sudden_overconsumption`: the compressor rises 35 percent above expected and produces a fixed-contract anomaly record.
- `device_dropout`: the pump stops producing records halfway through the run.
- `meter_reset`: the heater counter resets once and a `meter.reset` system event records the boundary. All other counters and all normal-scenario counters remain monotonic.

Forecasts use the stable forecast schema and are clearly labelled with a `simulator-v1-seed-*` model version; they are not presented as trained ML output.

## Commands

Set the required API environment variables, migrate the database, then run from `apps/api`:

```powershell
..\..\.venv\Scripts\python.exe -m app.simulator.cli seed
..\..\.venv\Scripts\python.exe -m app.simulator.cli generate `
  --start 2026-08-15T10:00:00Z --seconds 60 --scenario normal --persist
```

Omit `--persist` to generate and validate a summary without changing the database. The generator requires a timezone-aware start timestamp.
