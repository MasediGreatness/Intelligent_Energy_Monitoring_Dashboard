from datetime import UTC, datetime

import pytest

from app.schemas.measurement import MeasurementRecord
from app.simulator import Scenario, generate_simulation

START = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)


def test_same_seed_and_range_produce_identical_records() -> None:
    first = generate_simulation(START, 12, seed=118)
    second = generate_simulation(START, 12, seed=118)
    assert first == second


def test_normal_energy_is_monotonic_per_device() -> None:
    result = generate_simulation(START, 20)
    by_device: dict[str, list[object]] = {}
    for record in result.measurements:
        by_device.setdefault(record.device_code, []).append(record.energy_kwh_total)
    for values in by_device.values():
        assert values == sorted(values)  # type: ignore[type-var]


@pytest.mark.parametrize("scenario", list(Scenario))
def test_every_documented_scenario_is_selectable(scenario: Scenario) -> None:
    result = generate_simulation(START, 20, scenario=scenario)
    assert result.forecasts


def test_scenarios_have_expected_distinguishing_evidence() -> None:
    normal = generate_simulation(START, 20)
    peak = generate_simulation(START, 20, scenario=Scenario.PEAK_DEMAND)
    low_pf = generate_simulation(START, 20, scenario=Scenario.LOW_POWER_FACTOR)
    dropout = generate_simulation(START, 20, scenario=Scenario.DEVICE_DROPOUT)
    reset = generate_simulation(START, 20, scenario=Scenario.METER_RESET)
    abnormal = generate_simulation(START, 20, scenario=Scenario.SUDDEN_OVERCONSUMPTION)

    assert sum(item.active_power_kw or 0 for item in peak.measurements) > sum(
        item.active_power_kw or 0 for item in normal.measurements
    )
    assert (
        min(
            item.power_factor or 1
            for item in low_pf.measurements
            if item.device_code == "LOAD-002"
        )
        < 0.8
    )
    assert len(dropout.measurements) < len(normal.measurements)
    assert [event.event_type for event in reset.events] == ["meter.reset"]
    assert abnormal.anomalies[0].actual_value == pytest.approx(
        abnormal.anomalies[0].expected_value * 1.35, abs=0.01
    )  # type: ignore[operator]


def test_public_measurement_contract_has_no_simulator_only_fields() -> None:
    expected = {
        "device_code",
        "measured_at",
        "voltage_v",
        "current_a",
        "active_power_kw",
        "reactive_power_kvar",
        "apparent_power_kva",
        "power_factor",
        "frequency_hz",
        "energy_kwh_total",
        "data_quality",
    }
    assert set(MeasurementRecord.model_fields) == expected
    sample = generate_simulation(START, 1).measurements[0].model_dump()
    assert "scenario" not in sample
    assert "seed" not in sample
