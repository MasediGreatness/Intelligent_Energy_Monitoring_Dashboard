from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from app.schemas.calculations import (
    DeviceStatus,
    ElectricalSample,
    EnergyResult,
    IntervalDemandResult,
    LatestDeviceValue,
)
from app.services.calculations import (
    aggregate_power,
    compare_equal_periods,
    current_demand,
    data_completeness,
    device_status,
    energy_from_counter,
    estimated_cost,
    peak_demand,
    time_weighted_demand,
)

NOW = datetime(2026, 8, 15, 12, tzinfo=UTC)
DEVICE_1 = UUID("00000000-0000-0000-0000-000000000001")
DEVICE_2 = UUID("00000000-0000-0000-0000-000000000002")
DEVICE_3 = UUID("00000000-0000-0000-0000-000000000003")


def sample(
    seconds: int,
    *,
    power: float | None = None,
    energy: str | None = None,
    quality: str = "good",
) -> ElectricalSample:
    return ElectricalSample(
        device_id=DEVICE_1,
        measured_at=NOW + timedelta(seconds=seconds),
        active_power_kw=power,
        energy_kwh_total=Decimal(energy) if energy is not None else None,
        data_quality=quality,
    )


@pytest.mark.parametrize(
    ("enabled", "age", "expected"),
    [
        (False, None, DeviceStatus.DISABLED),
        (True, None, DeviceStatus.OFFLINE),
        (True, 10, DeviceStatus.ONLINE),
        (True, 11, DeviceStatus.STALE),
        (True, 60, DeviceStatus.STALE),
        (True, 61, DeviceStatus.OFFLINE),
    ],
)
def test_device_status_boundaries(
    enabled: bool, age: int | None, expected: DeviceStatus
) -> None:
    latest_at = NOW - timedelta(seconds=age) if age is not None else None
    assert device_status(enabled=enabled, latest_at=latest_at, now=NOW) == expected


def test_current_demand_excludes_stale_missing_and_disabled() -> None:
    result = current_demand(
        [
            LatestDeviceValue(
                device_id=DEVICE_1, enabled=True, sample=sample(-5, power=12.5)
            ),
            LatestDeviceValue(
                device_id=DEVICE_2,
                enabled=True,
                sample=sample(-61, power=99),
            ),
            LatestDeviceValue(device_id=DEVICE_3, enabled=True, sample=None),
        ],
        now=NOW,
    )
    assert result.value_kw == 12.5
    assert result.included_devices == 1
    assert result.excluded_devices == 2
    assert result.excluded_device_ids == [DEVICE_2, DEVICE_3]


def test_current_demand_reports_no_data_instead_of_zero() -> None:
    result = current_demand(
        [LatestDeviceValue(device_id=DEVICE_1, enabled=True, sample=None)], now=NOW
    )
    assert result.value_kw is None


def test_energy_counter_handles_baseline_and_reset() -> None:
    result = energy_from_counter(
        [
            sample(-300, energy="100"),
            sample(300, energy="102"),
            sample(600, energy="1"),
            sample(900, energy="3"),
        ],
        period_start=NOW,
        period_end=NOW + timedelta(minutes=20),
    )
    assert result.energy_kwh == Decimal("4")
    assert result.baseline_at == NOW - timedelta(minutes=5)
    assert result.baseline_gap is False
    assert result.reset_count == 1
    assert result.valid_segments == 2


def test_energy_counter_flags_missing_baseline() -> None:
    result = energy_from_counter(
        [sample(300, energy="10"), sample(600, energy="11")],
        period_start=NOW,
        period_end=NOW + timedelta(minutes=15),
    )
    assert result.energy_kwh == Decimal("1")
    assert result.baseline_gap is True


def test_energy_counter_ignores_missing_counter_without_fabricating_zero() -> None:
    result = energy_from_counter(
        [
            sample(-60, energy="10"),
            sample(0, energy=None),
            sample(60, energy="12"),
            sample(120, energy="13"),
        ],
        period_start=NOW,
        period_end=NOW + timedelta(minutes=3),
    )
    assert result.energy_kwh == Decimal("3")
    assert result.valid_segments == 1


def test_completeness_counts_missing_samples_and_gaps() -> None:
    result = data_completeness(
        [sample(0, power=1), sample(1, power=1), sample(4, power=1)],
        period_start=NOW,
        period_end=NOW + timedelta(seconds=6),
    )
    assert result.expected_samples == 6
    assert result.valid_samples == 3
    assert result.completeness_pct == 50
    assert result.gap_count == 2


def test_fifteen_minute_time_weighted_demand_matches_fixture() -> None:
    result = time_weighted_demand(
        [sample(0, power=10), sample(300, power=20), sample(600, power=30)],
        window_start=NOW,
        window_end=NOW + timedelta(minutes=15),
        expected_sample_seconds=300,
    )
    assert result.demand_kw == 20
    assert result.covered_seconds == 900
    assert result.completeness_pct == 100


def test_peak_excludes_incomplete_intervals() -> None:
    def interval(
        minutes: int, demand: float, completeness: float
    ) -> IntervalDemandResult:
        start = NOW + timedelta(minutes=minutes)
        return IntervalDemandResult(
            window_start=start,
            window_end=start + timedelta(minutes=15),
            demand_kw=demand,
            covered_seconds=900 * completeness / 100,
            completeness_pct=completeness,
        )

    result = peak_demand(
        [interval(0, 40, 100), interval(15, 50, 80), interval(30, 45, 100)]
    )
    assert result.peak_demand_kw == 45
    assert result.peak_demand_at == NOW + timedelta(minutes=45)


def test_peak_and_cost_preserve_missing_data() -> None:
    incomplete = IntervalDemandResult(
        window_start=NOW,
        window_end=NOW + timedelta(minutes=15),
        demand_kw=50,
        covered_seconds=450,
        completeness_pct=50,
    )
    peak = peak_demand([incomplete])
    assert peak.peak_demand_kw is None
    assert peak.peak_demand_at is None
    assert estimated_cost(None, Decimal("3")) is None


def test_equal_period_comparison_and_cost() -> None:
    current = EnergyResult(
        energy_kwh=Decimal("120"),
        baseline_at=NOW,
        baseline_gap=False,
        reset_count=0,
        valid_segments=1,
    )
    previous = current.model_copy(update={"energy_kwh": Decimal("100")})
    assert compare_equal_periods(current, previous).change_pct == 20
    assert estimated_cost(Decimal("12.345"), Decimal("3")) == Decimal("37.04")
    zero = previous.model_copy(update={"energy_kwh": Decimal("0")})
    assert compare_equal_periods(current, zero).change_pct is None


def test_aggregation_exposes_counts_completeness_and_empty_buckets() -> None:
    samples = [sample(i, power=float(i + 1)) for i in range(10)]
    samples.extend(sample(10 + i, power=10) for i in range(5))
    result = aggregate_power(
        samples,
        period_start=NOW,
        period_end=NOW + timedelta(seconds=30),
        interval="10s",
    )
    actual = [(item.value, item.sample_count, item.completeness_pct) for item in result]
    assert actual == [
        (5.5, 10, 100),
        (10, 5, 50),
        (None, 0, 0),
    ]


@pytest.mark.parametrize("interval", ["raw", "10s", "1m", "15m", "1h", "1d"])
def test_all_required_aggregation_intervals(interval: str) -> None:
    result = aggregate_power(
        [sample(0, power=7)],
        period_start=NOW,
        period_end=NOW + timedelta(seconds=1),
        interval=interval,  # type: ignore[arg-type]
    )
    assert result[0].bucket_at <= NOW
    assert result[0].value == 7
