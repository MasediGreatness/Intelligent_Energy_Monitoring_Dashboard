"""Single source of truth for displayed engineering metrics."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal, cast
from uuid import UUID

from app.schemas.calculations import (
    AggregateBucket,
    CompletenessResult,
    DemandResult,
    DeviceStatus,
    ElectricalSample,
    EnergyResult,
    IntervalDemandResult,
    LatestDeviceValue,
    PeakDemandResult,
    PeriodComparisonResult,
)

AGGREGATION_SECONDS = {
    "10s": 10,
    "1m": 60,
    "15m": 900,
    "1h": 3600,
    "1d": 86400,
}
AggregationInterval = Literal["raw", "10s", "1m", "15m", "1h", "1d"]


def device_status(
    *,
    enabled: bool,
    latest_at: datetime | None,
    now: datetime,
    online_timeout_seconds: int = 10,
    stale_timeout_seconds: int = 60,
) -> DeviceStatus:
    if not enabled:
        return DeviceStatus.DISABLED
    if latest_at is None:
        return DeviceStatus.OFFLINE
    age_seconds = max(0.0, (now - latest_at).total_seconds())
    if age_seconds <= online_timeout_seconds:
        return DeviceStatus.ONLINE
    if age_seconds <= stale_timeout_seconds:
        return DeviceStatus.STALE
    return DeviceStatus.OFFLINE


def current_demand(
    devices: list[LatestDeviceValue],
    *,
    now: datetime,
    stale_timeout_seconds: int = 60,
) -> DemandResult:
    total = 0.0
    included = 0
    excluded: list[UUID] = []
    for device in devices:
        sample = device.sample
        if (
            not device.enabled
            or sample is None
            or sample.active_power_kw is None
            or sample.data_quality == "missing"
            or (now - sample.measured_at).total_seconds() > stale_timeout_seconds
        ):
            excluded.append(device.device_id)
            continue
        total += sample.active_power_kw
        included += 1
    return DemandResult(
        value_kw=round(total, 6) if included else None,
        included_devices=included,
        excluded_devices=len(excluded),
        excluded_device_ids=excluded,
    )


def energy_from_counter(
    samples: list[ElectricalSample],
    *,
    period_start: datetime,
    period_end: datetime,
    maximum_baseline_age: timedelta = timedelta(minutes=15),
) -> EnergyResult:
    valid = sorted(
        (
            item
            for item in samples
            if item.energy_kwh_total is not None
            and item.data_quality != "missing"
            and item.measured_at <= period_end
        ),
        key=lambda item: item.measured_at,
    )
    before = [item for item in valid if item.measured_at <= period_start]
    after = [item for item in valid if item.measured_at > period_start]
    baseline = before[-1] if before else (after[0] if after else None)
    if baseline is None:
        return EnergyResult(
            energy_kwh=None,
            baseline_at=None,
            baseline_gap=True,
            reset_count=0,
            valid_segments=0,
        )
    baseline_gap = (
        baseline.measured_at > period_start
        or period_start - baseline.measured_at > maximum_baseline_age
    )
    sequence = [baseline] + [
        item for item in after if item.measured_at > baseline.measured_at
    ]
    total = Decimal("0")
    resets = 0
    segments = 0
    previous = cast(Decimal, sequence[0].energy_kwh_total)
    for item in sequence[1:]:
        current = cast(Decimal, item.energy_kwh_total)
        delta = current - previous
        if delta < 0:
            resets += 1
            segments += 1
        else:
            total += delta
        previous = current
    if len(sequence) > 1:
        segments += 1
    return EnergyResult(
        energy_kwh=total,
        baseline_at=baseline.measured_at,
        baseline_gap=baseline_gap,
        reset_count=resets,
        valid_segments=segments,
    )


def data_completeness(
    samples: list[ElectricalSample],
    *,
    period_start: datetime,
    period_end: datetime,
    expected_sample_seconds: int = 1,
) -> CompletenessResult:
    duration = max(0.0, (period_end - period_start).total_seconds())
    expected = math.ceil(duration / expected_sample_seconds)
    valid_times = sorted(
        {
            item.measured_at
            for item in samples
            if period_start <= item.measured_at < period_end
            and item.data_quality != "missing"
            and item.active_power_kw is not None
        }
    )
    valid_count = min(len(valid_times), expected)
    gaps = 0
    previous = period_start - timedelta(seconds=expected_sample_seconds)
    for timestamp in valid_times:
        missing_between = (
            int((timestamp - previous).total_seconds() // expected_sample_seconds) - 1
        )
        if missing_between > 0:
            gaps += 1
        previous = timestamp
    if valid_count < expected and (
        not valid_times
        or period_end - valid_times[-1] > timedelta(seconds=expected_sample_seconds)
    ):
        gaps += 1
    percentage = (valid_count / expected * 100) if expected else 100.0
    return CompletenessResult(
        expected_samples=expected,
        valid_samples=valid_count,
        completeness_pct=round(percentage, 3),
        gap_count=gaps,
    )


def time_weighted_demand(
    samples: list[ElectricalSample],
    *,
    window_start: datetime,
    window_end: datetime,
    expected_sample_seconds: int = 1,
) -> IntervalDemandResult:
    ordered = sorted(
        (
            item
            for item in samples
            if window_start <= item.measured_at < window_end
            and item.active_power_kw is not None
            and item.data_quality != "missing"
        ),
        key=lambda item: item.measured_at,
    )
    weighted_kwh_seconds = 0.0
    covered_seconds = 0.0
    for index, sample in enumerate(ordered):
        power_kw = sample.active_power_kw
        assert power_kw is not None
        natural_end = (
            ordered[index + 1].measured_at if index + 1 < len(ordered) else window_end
        )
        coverage_end = min(
            natural_end,
            sample.measured_at + timedelta(seconds=expected_sample_seconds),
            window_end,
        )
        seconds = max(0.0, (coverage_end - sample.measured_at).total_seconds())
        weighted_kwh_seconds += power_kw * seconds
        covered_seconds += seconds
    duration = max(0.0, (window_end - window_start).total_seconds())
    return IntervalDemandResult(
        window_start=window_start,
        window_end=window_end,
        demand_kw=(
            round(weighted_kwh_seconds / covered_seconds, 6)
            if covered_seconds
            else None
        ),
        covered_seconds=covered_seconds,
        completeness_pct=round(covered_seconds / duration * 100, 3)
        if duration
        else 100.0,
    )


def peak_demand(
    intervals: list[IntervalDemandResult],
    *,
    interval_minutes: int = 15,
    minimum_completeness_pct: float = 90.0,
) -> PeakDemandResult:
    valid = [
        (item.demand_kw, item)
        for item in intervals
        if item.demand_kw is not None
        and item.completeness_pct >= minimum_completeness_pct
    ]
    if not valid:
        return PeakDemandResult(
            peak_demand_kw=None,
            peak_demand_at=None,
            interval_minutes=interval_minutes,
        )
    peak_value, highest = max(valid, key=lambda candidate: candidate[0])
    return PeakDemandResult(
        peak_demand_kw=peak_value,
        peak_demand_at=highest.window_end,
        interval_minutes=interval_minutes,
    )


def compare_equal_periods(
    current: EnergyResult, previous: EnergyResult
) -> PeriodComparisonResult:
    change = None
    if (
        current.energy_kwh is not None
        and previous.energy_kwh is not None
        and previous.energy_kwh != 0
    ):
        change = float(
            (current.energy_kwh - previous.energy_kwh)
            / previous.energy_kwh
            * Decimal("100")
        )
    return PeriodComparisonResult(
        current_kwh=current.energy_kwh,
        previous_kwh=previous.energy_kwh,
        change_pct=round(change, 3) if change is not None else None,
    )


def estimated_cost(energy_kwh: Decimal | None, tariff_zar: Decimal) -> Decimal | None:
    if energy_kwh is None:
        return None
    return (energy_kwh * tariff_zar).quantize(Decimal("0.01"))


def aggregate_power(
    samples: list[ElectricalSample],
    *,
    period_start: datetime,
    period_end: datetime,
    interval: AggregationInterval,
    expected_sample_seconds: int = 1,
) -> list[AggregateBucket]:
    valid = [item for item in samples if period_start <= item.measured_at < period_end]
    if interval == "raw":
        return [
            AggregateBucket(
                bucket_at=item.measured_at,
                value=item.active_power_kw if item.data_quality != "missing" else None,
                sample_count=1 if item.data_quality != "missing" else 0,
                completeness_pct=100.0 if item.data_quality != "missing" else 0.0,
            )
            for item in sorted(valid, key=lambda sample: sample.measured_at)
        ]
    bucket_seconds = AGGREGATION_SECONDS[interval]
    grouped: dict[datetime, list[ElectricalSample]] = defaultdict(list)
    for item in valid:
        epoch = int(item.measured_at.astimezone(UTC).timestamp())
        bucket_epoch = epoch - epoch % bucket_seconds
        grouped[datetime.fromtimestamp(bucket_epoch, UTC)].append(item)
    expected = max(1, bucket_seconds // expected_sample_seconds)
    start_epoch = int(period_start.astimezone(UTC).timestamp())
    first_bucket_epoch = start_epoch - start_epoch % bucket_seconds
    output: list[AggregateBucket] = []
    bucket_at = datetime.fromtimestamp(first_bucket_epoch, UTC)
    while bucket_at < period_end:
        usable = [
            item.active_power_kw
            for item in grouped.get(bucket_at, [])
            if item.active_power_kw is not None and item.data_quality != "missing"
        ]
        output.append(
            AggregateBucket(
                bucket_at=bucket_at,
                value=round(sum(usable) / len(usable), 6) if usable else None,
                sample_count=len(usable),
                completeness_pct=round(min(len(usable), expected) / expected * 100, 3),
            )
        )
        bucket_at += timedelta(seconds=bucket_seconds)
    return output
