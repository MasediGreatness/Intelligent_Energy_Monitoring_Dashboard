"""Typed internal results for engineering calculations."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceStatus(StrEnum):
    ONLINE = "online"
    STALE = "stale"
    OFFLINE = "offline"
    DISABLED = "disabled"


class ElectricalSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: UUID
    measured_at: datetime
    active_power_kw: float | None = None
    energy_kwh_total: Decimal | None = None
    data_quality: str = "good"


class LatestDeviceValue(BaseModel):
    device_id: UUID
    enabled: bool
    sample: ElectricalSample | None


class DemandResult(BaseModel):
    value_kw: float | None
    included_devices: int
    excluded_devices: int
    excluded_device_ids: list[UUID]


class EnergyResult(BaseModel):
    energy_kwh: Decimal | None
    baseline_at: datetime | None
    baseline_gap: bool
    reset_count: int
    valid_segments: int


class CompletenessResult(BaseModel):
    expected_samples: int
    valid_samples: int
    completeness_pct: float = Field(ge=0, le=100)
    gap_count: int


class IntervalDemandResult(BaseModel):
    window_start: datetime
    window_end: datetime
    demand_kw: float | None
    covered_seconds: float
    completeness_pct: float


class PeakDemandResult(BaseModel):
    peak_demand_kw: float | None
    peak_demand_at: datetime | None
    interval_minutes: int


class PeriodComparisonResult(BaseModel):
    current_kwh: Decimal | None
    previous_kwh: Decimal | None
    change_pct: float | None


class AggregateBucket(BaseModel):
    bucket_at: datetime
    value: float | None
    sample_count: int
    completeness_pct: float
