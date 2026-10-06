"""Bounded measurement history queries."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models import Measurement
from app.schemas.calculations import ElectricalSample


def measurement_history(
    session: Session,
    *,
    device_ids: list[UUID],
    period_start: datetime,
    period_end: datetime,
    raw: bool,
) -> list[ElectricalSample]:
    duration = period_end - period_start
    if period_end <= period_start:
        raise ApplicationError(
            status_code=422,
            code="INVALID_DATE_RANGE",
            message="The end timestamp must be after the start timestamp.",
        )
    if duration > timedelta(days=31) or (raw and duration > timedelta(hours=24)):
        raise ApplicationError(
            status_code=422,
            code="HISTORY_RANGE_EXCEEDED",
            message="The requested history range exceeds the allowed limit.",
        )
    rows = session.execute(
        select(
            Measurement.device_id,
            Measurement.measured_at,
            Measurement.active_power_kw,
            Measurement.energy_kwh_total,
            Measurement.data_quality,
        )
        .where(
            Measurement.device_id.in_(device_ids),
            Measurement.measured_at >= period_start,
            Measurement.measured_at < period_end,
        )
        .order_by(Measurement.measured_at)
    ).all()
    return [
        ElectricalSample(
            device_id=row.device_id,
            measured_at=row.measured_at,
            active_power_kw=row.active_power_kw,
            energy_kwh_total=row.energy_kwh_total,
            data_quality=row.data_quality.value,
        )
        for row in rows
    ]
