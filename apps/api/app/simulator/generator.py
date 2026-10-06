"""Repeatable measurement, forecast, anomaly, and connectivity generation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import uuid5

from app.schemas.anomaly import AnomalyRecord
from app.schemas.forecast import ForecastRecord
from app.schemas.measurement import MeasurementRecord
from app.simulator.catalog import DEVICES, SIMULATOR_NAMESPACE, DeviceDefinition


class Scenario(StrEnum):
    NORMAL = "normal"
    PEAK_DEMAND = "peak_demand"
    LOW_POWER_FACTOR = "low_power_factor"
    SUDDEN_OVERCONSUMPTION = "sudden_overconsumption"
    DEVICE_DROPOUT = "device_dropout"
    METER_RESET = "meter_reset"


@dataclass(frozen=True)
class SimulationEvent:
    event_at: datetime
    event_type: str
    entity_id: str
    details: dict[str, str]


@dataclass(frozen=True)
class SimulationResult:
    measurements: tuple[MeasurementRecord, ...]
    forecasts: tuple[ForecastRecord, ...]
    anomalies: tuple[AnomalyRecord, ...]
    events: tuple[SimulationEvent, ...]


def _noise(seed: int, code: str, timestamp: datetime, channel: str) -> float:
    payload = f"{seed}|{code}|{timestamp.isoformat()}|{channel}".encode()
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return (integer / (2**64 - 1)) * 2 - 1


def _base_load(device: DeviceDefinition, timestamp: datetime) -> float:
    local_hour = (timestamp.astimezone(UTC).hour + 2) % 24
    working = 6 <= local_hour < 22
    profiles = {
        "compressor": 0.68 if working else 0.25,
        "conveyor": 0.72 if 7 <= local_hour < 19 else 0.08,
        "pump": 0.48 if working else 0.20,
        "heater": 0.62 if 5 <= local_hour < 18 else 0.18,
        "lighting": 0.78 if local_hour >= 18 or local_hour < 6 else 0.22,
    }
    cycle = 1 + 0.08 * math.sin(timestamp.timestamp() / 90 + len(device.code))
    return device.rated_power_kw * profiles[device.profile] * cycle


def _scenario_multiplier(
    scenario: Scenario, progress: float, device: DeviceDefinition
) -> float:
    active = 0.35 <= progress <= 0.75
    if scenario == Scenario.PEAK_DEMAND and active:
        return 1.22
    if (
        scenario == Scenario.SUDDEN_OVERCONSUMPTION
        and active
        and device.code == "LOAD-001"
    ):
        return 1.35
    return 1.0


def generate_simulation(
    start: datetime, seconds: int, seed: int = 118, scenario: Scenario = Scenario.NORMAL
) -> SimulationResult:
    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("start must be timezone-aware")
    if seconds < 1:
        raise ValueError("seconds must be positive")
    start = start.astimezone(UTC)
    records: list[MeasurementRecord] = []
    events: list[SimulationEvent] = []
    latest_total_kw = 0.0

    for device in DEVICES:
        energy = Decimal(str(device.base_energy_kwh))
        reset_emitted = False
        for offset in range(seconds):
            timestamp = start + timedelta(seconds=offset)
            progress = offset / max(seconds - 1, 1)
            if (
                scenario == Scenario.DEVICE_DROPOUT
                and device.code == "LOAD-003"
                and progress >= 0.5
            ):
                continue

            expected_kw = _base_load(device, timestamp)
            power_kw = max(
                0.0,
                expected_kw
                * _scenario_multiplier(scenario, progress, device)
                * (1 + 0.015 * _noise(seed, device.code, timestamp, "power")),
            )
            pf = 0.96 + 0.01 * _noise(seed, device.code, timestamp, "pf")
            if (
                scenario == Scenario.LOW_POWER_FACTOR
                and device.code == "LOAD-002"
                and 0.35 <= progress <= 0.75
            ):
                pf = 0.72 + 0.01 * _noise(seed, device.code, timestamp, "pf-low")
            pf = min(1.0, max(0.01, pf))
            voltage = 230.0 + 1.8 * _noise(seed, device.code, timestamp, "voltage")
            apparent = power_kw / pf
            current = (
                apparent * 1000 / (math.sqrt(3) * voltage)
                if device.phase_type == "three_phase"
                else apparent * 1000 / voltage
            )
            reactive = math.sqrt(max(apparent**2 - power_kw**2, 0.0))

            if (
                scenario == Scenario.METER_RESET
                and device.code == "LOAD-004"
                and progress >= 0.5
                and not reset_emitted
            ):
                energy = Decimal("0")
                reset_emitted = True
                events.append(
                    SimulationEvent(
                        timestamp,
                        "meter.reset",
                        str(device.id),
                        {
                            "device_code": device.code,
                            "reason": "scripted simulator scenario",
                        },
                    )
                )

            energy += Decimal(str(power_kw)) / Decimal("3600")
            records.append(
                MeasurementRecord(
                    device_code=device.code,
                    measured_at=timestamp,
                    voltage_v=round(voltage, 3),
                    current_a=round(current, 4),
                    active_power_kw=round(power_kw, 4),
                    reactive_power_kvar=round(reactive, 4),
                    apparent_power_kva=round(apparent, 4),
                    power_factor=round(pf, 4),
                    frequency_hz=round(
                        50 + 0.025 * _noise(seed, device.code, timestamp, "frequency"),
                        4,
                    ),
                    energy_kwh_total=energy.quantize(Decimal("0.000001")),
                    data_quality="good",
                )
            )

    if records:
        last_time = start + timedelta(seconds=seconds - 1)
        latest_total_kw = sum(
            record.active_power_kw or 0
            for record in records
            if record.measured_at == last_time
        )
    generated_at = start + timedelta(seconds=seconds - 1)
    forecasts = tuple(
        ForecastRecord(
            generated_at=generated_at,
            target_at=generated_at + timedelta(minutes=minute),
            horizon_minutes=minute,
            predicted_power_kw=round(
                latest_total_kw * (1 + 0.015 * math.sin(minute / 4)), 3
            ),
            lower_kw=round(latest_total_kw * 0.94, 3),
            upper_kw=round(latest_total_kw * 1.06, 3),
            model_version=f"simulator-v1-seed-{seed}",
        )
        for minute in (5, 10, 15, 30, 60)
    )

    anomalies: tuple[AnomalyRecord, ...] = ()
    if scenario == Scenario.SUDDEN_OVERCONSUMPTION:
        device = DEVICES[0]
        detected_at = start + timedelta(seconds=max(0, int(seconds * 0.35)))
        expected = _base_load(device, detected_at)
        actual = expected * 1.35
        anomalies = (
            AnomalyRecord(
                id=uuid5(
                    SIMULATOR_NAMESPACE,
                    f"{seed}|{scenario}|{detected_at.isoformat()}|{device.code}",
                ),
                device_id=device.id,
                detected_at=detected_at,
                anomaly_type="sudden_overconsumption",
                severity="high",
                metric="active_power_kw",
                actual_value=round(actual, 3),
                expected_value=round(expected, 3),
                score=0.91,
                explanation=(
                    "Simulated compressor demand is 35 percent above its "
                    "expected profile."
                ),
            ),
        )

    return SimulationResult(tuple(records), forecasts, anomalies, tuple(events))
