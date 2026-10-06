"""Versioned, typed REST read endpoints used by the dashboard."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.errors import ApplicationError
from app.db.session import get_db_session
from app.models import (
    Alarm,
    Anomaly,
    Device,
    Forecast,
    Measurement,
    Setting,
    SystemEvent,
)
from app.models.enums import AnomalyStatus, LifecycleStatus, Severity
from app.schemas.calculations import ElectricalSample, LatestDeviceValue
from app.schemas.read import (
    AlarmItem,
    AnomalyItem,
    CountByDeviceStatus,
    CountBySeverity,
    DailyEnergyItem,
    DailyEnergyResponse,
    DashboardSummary,
    DeviceItem,
    EventItem,
    ForecastItem,
    ForecastResponse,
    HistoryPoint,
    HistoryResponse,
    HistorySeries,
    LatestMeasurement,
    Page,
    SettingItem,
)
from app.services.calculations import (
    AggregationInterval,
    aggregate_power,
    current_demand,
    data_completeness,
    device_status,
    energy_from_counter,
)

ERROR_EXAMPLE = {
    "error": {
        "code": "INVALID_DATE_RANGE",
        "message": "The end timestamp must be after the start timestamp.",
        "details": {"field": "to"},
        "request_id": "01J5EXAMPLE",
    }
}
router = APIRouter(
    prefix="/api/v1",
    tags=["dashboard reads"],
    dependencies=[Depends(current_user)],
    responses={
        422: {
            "description": "Invalid query parameters",
            "content": {"application/json": {"example": ERROR_EXAMPLE}},
        }
    },
)
DbSession = Annotated[Session, Depends(get_db_session)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=200)]
Metric = Literal[
    "voltage_v",
    "current_a",
    "active_power_kw",
    "reactive_power_kvar",
    "apparent_power_kva",
    "power_factor",
    "frequency_hz",
    "energy_kwh_total",
]


def _status_timeouts(session: Session) -> tuple[int, int]:
    values = {
        row.key: row.value_json
        for row in session.scalars(
            select(Setting).where(
                Setting.key.in_(["online_timeout_seconds", "stale_timeout_seconds"])
            )
        )
    }
    online = values.get("online_timeout_seconds", 10)
    stale = values.get("stale_timeout_seconds", 60)
    return (
        online if isinstance(online, int) else 10,
        stale if isinstance(stale, int) else 60,
    )


def _timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ApplicationError(
            status_code=422,
            code="INVALID_TIMEZONE",
            message="The requested timezone is not recognised.",
            details={"field": "timezone"},
        ) from exc


def _samples(
    rows: list[Measurement], metric: Metric = "active_power_kw"
) -> list[ElectricalSample]:
    return [
        ElectricalSample(
            device_id=row.device_id,
            measured_at=row.measured_at,
            active_power_kw=(
                float(value) if (value := getattr(row, metric)) is not None else None
            ),
            energy_kwh_total=row.energy_kwh_total,
            data_quality=row.data_quality.value,
        )
        for row in rows
    ]


@router.get("/measurements/latest", response_model=list[LatestMeasurement])
def latest_measurements(
    session: DbSession,
    device_id: Annotated[list[UUID] | None, Query()] = None,
) -> list[LatestMeasurement]:
    now = datetime.now(UTC)
    online_timeout, stale_timeout = _status_timeouts(session)
    devices = list(session.scalars(select(Device).order_by(Device.code)))
    if device_id:
        devices = [item for item in devices if item.id in device_id]
    result: list[LatestMeasurement] = []
    for device in devices:
        latest = session.scalar(
            select(Measurement)
            .where(Measurement.device_id == device.id)
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        result.append(
            LatestMeasurement(
                device_id=device.id,
                device_code=device.code,
                measured_at=latest.measured_at if latest else None,
                active_power_kw=latest.active_power_kw if latest else None,
                voltage_v=latest.voltage_v if latest else None,
                current_a=latest.current_a if latest else None,
                power_factor=latest.power_factor if latest else None,
                frequency_hz=latest.frequency_hz if latest else None,
                data_quality=latest.data_quality.value if latest else None,
                status=device_status(
                    enabled=device.enabled,
                    latest_at=latest.measured_at if latest else None,
                    now=now,
                    online_timeout_seconds=online_timeout,
                    stale_timeout_seconds=stale_timeout,
                ),
            )
        )
    return result


@router.get("/measurements/history", response_model=HistoryResponse)
def measurement_history(
    session: DbSession,
    device_id: Annotated[list[UUID], Query(min_length=1)],
    from_at: Annotated[datetime, Query(alias="from")],
    to_at: Annotated[datetime, Query(alias="to")],
    interval: AggregationInterval,
    metric: Metric,
    timezone: str = "UTC",
) -> HistoryResponse:
    _timezone(timezone)
    duration = to_at - from_at
    if to_at <= from_at:
        raise ApplicationError(
            status_code=422,
            code="INVALID_DATE_RANGE",
            message="The end timestamp must be after the start timestamp.",
            details={"field": "to"},
        )
    if duration > timedelta(days=31) or (
        interval == "raw" and duration > timedelta(hours=24)
    ):
        raise ApplicationError(
            status_code=422,
            code="HISTORY_RANGE_EXCEEDED",
            message="The requested history range exceeds the allowed limit.",
        )
    series: list[HistorySeries] = []
    for identifier in device_id:
        rows = list(
            session.scalars(
                select(Measurement)
                .where(
                    Measurement.device_id == identifier,
                    Measurement.measured_at >= from_at,
                    Measurement.measured_at < to_at,
                )
                .order_by(Measurement.measured_at)
            )
        )
        points = aggregate_power(
            _samples(rows, metric),
            period_start=from_at,
            period_end=to_at,
            interval=interval,
        )
        series.append(
            HistorySeries(
                device_id=identifier,
                metric=metric,
                interval=interval,
                points=[
                    HistoryPoint.model_validate(item, from_attributes=True)
                    for item in points
                ],
            )
        )
    return HistoryResponse(timezone=timezone, series=series)


@router.get("/energy/daily", response_model=DailyEnergyResponse)
def daily_energy(
    session: DbSession,
    from_date: date,
    to_date: date,
    timezone: str = "UTC",
    device_id: UUID | None = None,
) -> DailyEnergyResponse:
    zone = _timezone(timezone)
    if to_date < from_date or (to_date - from_date).days > 31:
        raise ApplicationError(
            status_code=422,
            code="INVALID_DATE_RANGE",
            message="The requested date range is invalid.",
        )
    identifiers = [device_id] if device_id else list(session.scalars(select(Device.id)))
    output: list[DailyEnergyItem] = []
    day = from_date
    while day <= to_date:
        start = datetime.combine(day, time.min, zone).astimezone(UTC)
        end = (datetime.combine(day, time.min, zone) + timedelta(days=1)).astimezone(
            UTC
        )
        for identifier in identifiers:
            rows = list(
                session.scalars(
                    select(Measurement)
                    .where(
                        Measurement.device_id == identifier,
                        Measurement.measured_at >= start - timedelta(minutes=15),
                        Measurement.measured_at < end,
                    )
                    .order_by(Measurement.measured_at)
                )
            )
            samples = _samples(rows)
            energy = energy_from_counter(samples, period_start=start, period_end=end)
            buckets = aggregate_power(
                samples, period_start=start, period_end=end, interval="15m"
            )
            complete_values = [
                item.value
                for item in buckets
                if item.value is not None and item.completeness_pct >= 90
            ]
            peak = max(complete_values, default=None)
            completeness = data_completeness(
                samples, period_start=start, period_end=end
            )
            output.append(
                DailyEnergyItem(
                    day=day,
                    device_id=identifier,
                    energy_kwh=energy.energy_kwh,
                    peak_demand_kw=peak,
                    completeness_pct=completeness.completeness_pct,
                )
            )
        day += timedelta(days=1)
    return DailyEnergyResponse(timezone=timezone, items=output)


@router.get("/forecasts/latest", response_model=ForecastResponse)
def latest_forecast(
    session: DbSession,
    horizon_minutes: Annotated[int, Query(gt=0)],
    device_id: UUID | None = None,
) -> ForecastResponse:
    statement = select(Forecast).where(Forecast.horizon_minutes == horizon_minutes)
    if device_id is not None:
        statement = statement.where(Forecast.device_id == device_id)
    latest_generated = session.scalar(
        select(func.max(Forecast.generated_at)).where(
            Forecast.horizon_minutes == horizon_minutes
        )
    )
    if latest_generated is not None:
        statement = statement.where(Forecast.generated_at == latest_generated)
    rows = session.scalars(statement.order_by(Forecast.target_at)).all()
    return ForecastResponse(
        items=[ForecastItem.model_validate(row, from_attributes=True) for row in rows]
    )


@router.get("/anomalies", response_model=Page[AnomalyItem])
def anomalies(
    session: DbSession,
    page: PageNumber = 1,
    page_size: PageSize = 50,
    status: AnomalyStatus | None = None,
    severity: Severity | None = None,
    device_id: UUID | None = None,
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
) -> Page[AnomalyItem]:
    statement = select(Anomaly)
    for condition in (
        Anomaly.status == status if status else None,
        Anomaly.severity == severity if severity else None,
        Anomaly.device_id == device_id if device_id else None,
        Anomaly.detected_at >= from_at if from_at else None,
        Anomaly.detected_at < to_at if to_at else None,
    ):
        if condition is not None:
            statement = statement.where(condition)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.scalars(
        statement.order_by(Anomaly.detected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        page=page,
        page_size=page_size,
        total=total,
        items=[AnomalyItem.model_validate(row) for row in rows],
    )


@router.get("/alarms", response_model=Page[AlarmItem])
def alarms(
    session: DbSession,
    page: PageNumber = 1,
    page_size: PageSize = 50,
    status: LifecycleStatus | None = None,
    severity: Severity | None = None,
    device_id: UUID | None = None,
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
) -> Page[AlarmItem]:
    statement = select(Alarm)
    for condition in (
        Alarm.status == status if status else None,
        Alarm.severity == severity if severity else None,
        Alarm.device_id == device_id if device_id else None,
        Alarm.triggered_at >= from_at if from_at else None,
        Alarm.triggered_at < to_at if to_at else None,
    ):
        if condition is not None:
            statement = statement.where(condition)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.scalars(
        statement.order_by(Alarm.triggered_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        page=page,
        page_size=page_size,
        total=total,
        items=[AlarmItem.model_validate(row) for row in rows],
    )


@router.get("/devices", response_model=Page[DeviceItem])
def devices(
    session: DbSession,
    page: PageNumber = 1,
    page_size: PageSize = 50,
    enabled: bool | None = None,
) -> Page[DeviceItem]:
    statement = select(Device)
    if enabled is not None:
        statement = statement.where(Device.enabled == enabled)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.scalars(
        statement.order_by(Device.code).offset((page - 1) * page_size).limit(page_size)
    ).all()
    now = datetime.now(UTC)
    online_timeout, stale_timeout = _status_timeouts(session)
    return Page(
        page=page,
        page_size=page_size,
        total=total,
        items=[
            DeviceItem(
                id=row.id,
                code=row.code,
                name=row.name,
                location=row.location,
                phase_type=row.phase_type,
                rated_power_kw=row.rated_power_kw,
                criticality=row.criticality,
                enabled=row.enabled,
                last_seen_at=row.last_seen_at,
                status=device_status(
                    enabled=row.enabled,
                    latest_at=row.last_seen_at,
                    now=now,
                    online_timeout_seconds=online_timeout,
                    stale_timeout_seconds=stale_timeout,
                ),
            )
            for row in rows
        ],
    )


@router.get("/settings", response_model=list[SettingItem])
def settings(session: DbSession) -> list[SettingItem]:
    return [
        SettingItem.model_validate(row)
        for row in session.scalars(select(Setting).order_by(Setting.key))
    ]


@router.get("/events", response_model=Page[EventItem])
def events(
    session: DbSession,
    page: PageNumber = 1,
    page_size: PageSize = 50,
    event_type: str | None = None,
) -> Page[EventItem]:
    statement = select(SystemEvent)
    if event_type:
        statement = statement.where(SystemEvent.event_type == event_type)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.scalars(
        statement.order_by(SystemEvent.event_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        page=page,
        page_size=page_size,
        total=total,
        items=[EventItem.model_validate(row) for row in rows],
    )


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    session: DbSession, timezone: str = "Africa/Johannesburg"
) -> DashboardSummary:
    zone = _timezone(timezone)
    now = datetime.now(UTC)
    online_timeout, stale_timeout = _status_timeouts(session)
    local_day = now.astimezone(zone).date()
    start = datetime.combine(local_day, time.min, zone).astimezone(UTC)
    comparison_at = now - timedelta(minutes=15)
    previous_start = datetime.combine(
        local_day - timedelta(days=1), time.min, zone
    ).astimezone(UTC)
    previous_end = (now.astimezone(zone) - timedelta(days=1)).astimezone(UTC)
    devices = list(session.scalars(select(Device).order_by(Device.code)))
    latest_values: list[LatestDeviceValue] = []
    comparison_values: list[LatestDeviceValue] = []
    status_counts = CountByDeviceStatus()
    energy_total = Decimal("0")
    energy_available = False
    previous_energy_total = Decimal("0")
    previous_energy_available = False
    completeness_values: list[float] = []
    power_by_timestamp: dict[datetime, float] = {}
    for device in devices:
        latest = session.scalar(
            select(Measurement)
            .where(Measurement.device_id == device.id)
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        latest_sample = _samples([latest])[0] if latest else None
        latest_values.append(
            LatestDeviceValue(
                device_id=device.id, enabled=device.enabled, sample=latest_sample
            )
        )
        comparison_measurement = session.scalar(
            select(Measurement)
            .where(
                Measurement.device_id == device.id,
                Measurement.measured_at <= comparison_at,
            )
            .order_by(Measurement.measured_at.desc())
            .limit(1)
        )
        comparison_values.append(
            LatestDeviceValue(
                device_id=device.id,
                enabled=device.enabled,
                sample=(
                    _samples([comparison_measurement])[0]
                    if comparison_measurement
                    else None
                ),
            )
        )
        status = device_status(
            enabled=device.enabled,
            latest_at=latest.measured_at if latest else None,
            now=now,
            online_timeout_seconds=online_timeout,
            stale_timeout_seconds=stale_timeout,
        )
        setattr(status_counts, status.value, getattr(status_counts, status.value) + 1)
        rows = list(
            session.scalars(
                select(Measurement)
                .where(
                    Measurement.device_id == device.id,
                    Measurement.measured_at >= start - timedelta(minutes=15),
                    Measurement.measured_at <= now,
                )
                .order_by(Measurement.measured_at)
            )
        )
        samples = _samples(rows)
        device_energy = energy_from_counter(samples, period_start=start, period_end=now)
        if device_energy.energy_kwh is not None:
            energy_total += device_energy.energy_kwh
            energy_available = True
        previous_rows = list(
            session.scalars(
                select(Measurement)
                .where(
                    Measurement.device_id == device.id,
                    Measurement.measured_at >= previous_start - timedelta(minutes=15),
                    Measurement.measured_at <= previous_end,
                )
                .order_by(Measurement.measured_at)
            )
        )
        previous_energy = energy_from_counter(
            _samples(previous_rows),
            period_start=previous_start,
            period_end=previous_end,
        )
        if previous_energy.energy_kwh is not None:
            previous_energy_total += previous_energy.energy_kwh
            previous_energy_available = True
        completeness_values.append(
            data_completeness(
                samples, period_start=start, period_end=now
            ).completeness_pct
        )
        for item in samples:
            if (
                item.measured_at >= start
                and item.active_power_kw is not None
                and item.data_quality != "missing"
            ):
                power_by_timestamp[item.measured_at] = (
                    power_by_timestamp.get(item.measured_at, 0.0) + item.active_power_kw
                )
    demand = current_demand(latest_values, now=now, stale_timeout_seconds=stale_timeout)
    comparison_demand = current_demand(
        comparison_values,
        now=comparison_at,
        stale_timeout_seconds=stale_timeout,
    )
    current_demand_kw = demand.value_kw
    comparison_demand_kw = comparison_demand.value_kw
    demand_change_pct = (
        round(
            (current_demand_kw - comparison_demand_kw) / comparison_demand_kw * 100,
            3,
        )
        if current_demand_kw is not None
        and comparison_demand_kw is not None
        and comparison_demand_kw != 0
        else None
    )
    energy_change_pct = (
        round(
            float(
                (energy_total - previous_energy_total)
                / previous_energy_total
                * Decimal("100")
            ),
            3,
        )
        if energy_available and previous_energy_available and previous_energy_total != 0
        else None
    )
    total_power_samples = [
        ElectricalSample(
            device_id=UUID(int=0),
            measured_at=timestamp,
            active_power_kw=value,
        )
        for timestamp, value in power_by_timestamp.items()
    ]
    demand_buckets = aggregate_power(
        total_power_samples,
        period_start=start,
        period_end=now,
        interval="15m",
    )
    qualified_buckets = [
        item
        for item in demand_buckets
        if item.value is not None and item.completeness_pct >= 90
    ]
    peak_bucket = max(
        qualified_buckets,
        key=lambda item: item.value if item.value is not None else float("-inf"),
        default=None,
    )
    completeness_pct = (
        sum(completeness_values) / len(completeness_values)
        if completeness_values
        else 100.0
    )
    alarm_counts = CountBySeverity()
    for severity, count in session.execute(
        select(Alarm.severity, func.count())
        .where(Alarm.status != LifecycleStatus.CLEARED)
        .group_by(Alarm.severity)
    ):
        setattr(alarm_counts, severity.value, count)
    limit_setting = session.get(Setting, "demand_limit_kw")
    limit = (
        float(limit_setting.value_json)
        if limit_setting and isinstance(limit_setting.value_json, (int, float))
        else None
    )
    return DashboardSummary(
        generated_at=now,
        timezone=timezone,
        current_demand_kw=current_demand_kw,
        current_demand_change_pct=demand_change_pct,
        energy_today_kwh=energy_total if energy_available else None,
        energy_vs_previous_pct=energy_change_pct,
        peak_demand_kw=peak_bucket.value if peak_bucket else None,
        peak_demand_at=peak_bucket.bucket_at if peak_bucket else None,
        demand_limit_kw=limit,
        active_alarms=alarm_counts,
        devices=status_counts,
        data_completeness_pct=round(completeness_pct, 3),
        excluded_stale_devices=demand.excluded_devices,
    )
