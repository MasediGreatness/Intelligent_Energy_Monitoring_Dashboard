"""Stable response contracts for dashboard read APIs."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnomalyStatus,
    Criticality,
    LifecycleStatus,
    PhaseType,
    Severity,
)
from app.schemas.calculations import DeviceStatus


class Page[T](BaseModel):
    page: int
    page_size: int
    total: int
    items: list[T]


class LatestMeasurement(BaseModel):
    device_id: UUID
    device_code: str
    measured_at: datetime | None
    active_power_kw: float | None
    voltage_v: float | None
    current_a: float | None
    power_factor: float | None
    frequency_hz: float | None
    data_quality: str | None
    status: DeviceStatus


class HistoryPoint(BaseModel):
    bucket_at: datetime
    value: float | None
    sample_count: int
    completeness_pct: float


class HistorySeries(BaseModel):
    device_id: UUID
    metric: str
    interval: str
    points: list[HistoryPoint]


class HistoryResponse(BaseModel):
    timezone: str
    series: list[HistorySeries]


class DailyEnergyItem(BaseModel):
    day: date
    device_id: UUID | None
    energy_kwh: Decimal | None
    peak_demand_kw: float | None
    completeness_pct: float


class DailyEnergyResponse(BaseModel):
    timezone: str
    items: list[DailyEnergyItem]


class ForecastItem(BaseModel):
    device_id: UUID | None
    generated_at: datetime
    target_at: datetime
    horizon_minutes: int
    predicted_power_kw: float
    lower_kw: float | None
    upper_kw: float | None
    model_version: str


class ForecastResponse(BaseModel):
    items: list[ForecastItem]


class AnomalyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    detected_at: datetime
    anomaly_type: str
    severity: Severity
    metric: str
    actual_value: float | None
    expected_value: float | None
    score: float
    explanation: str
    status: AnomalyStatus


class AlarmItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID | None
    source: str
    alarm_type: str
    severity: Severity
    message: str
    triggered_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: UUID | None
    acknowledgement_note: str | None
    cleared_at: datetime | None
    status: LifecycleStatus


class DeviceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    location: str
    phase_type: PhaseType
    rated_power_kw: float
    criticality: Criticality
    enabled: bool
    last_seen_at: datetime | None
    status: DeviceStatus


class SettingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value_json: object
    description: str
    updated_at: datetime


class EventItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_at: datetime
    actor_user_id: UUID | None
    event_type: str
    entity_type: str | None
    entity_id: str | None
    details_json: dict[str, object]


class CountBySeverity(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class CountByDeviceStatus(BaseModel):
    online: int = 0
    stale: int = 0
    offline: int = 0
    disabled: int = 0


class DashboardSummary(BaseModel):
    generated_at: datetime
    timezone: str
    current_demand_kw: float | None
    current_demand_change_pct: float | None
    energy_today_kwh: Decimal | None
    energy_vs_previous_pct: float | None
    peak_demand_kw: float | None
    peak_demand_at: datetime | None
    demand_limit_kw: float | None
    active_alarms: CountBySeverity
    devices: CountByDeviceStatus
    data_completeness_pct: float = Field(ge=0, le=100)
    excluded_stale_devices: int
