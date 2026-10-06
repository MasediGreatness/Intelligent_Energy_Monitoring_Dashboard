"""Measurement persistence operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Device, Measurement, SystemEvent
from app.schemas.ingestion import MeasurementIngestRecord


def device_ids_by_code(session: Session, codes: set[str]) -> dict[str, UUID]:
    return {
        code: device_id
        for code, device_id in session.execute(
            select(Device.code, Device.id).where(Device.code.in_(codes))
        )
    }


def latest_energy_counter(session: Session, device_id: UUID) -> Decimal | None:
    return session.scalar(
        select(Measurement.energy_kwh_total)
        .where(
            Measurement.device_id == device_id,
            Measurement.energy_kwh_total.is_not(None),
        )
        .order_by(Measurement.measured_at.desc())
        .limit(1)
    )


def insert_measurement(
    session: Session, device_id: UUID, record: MeasurementIngestRecord
) -> bool:
    values = record.model_dump(exclude={"device_code", "energy_reset"})
    result = session.execute(
        insert(Measurement)
        .values(device_id=device_id, **values)
        .on_conflict_do_nothing(constraint="uq_measurements_device_measured_at")
        .returning(Measurement.id)
    )
    return result.scalar_one_or_none() is not None


def update_last_seen(session: Session, device_id: UUID, measured_at: datetime) -> None:
    session.execute(
        update(Device)
        .where(
            Device.id == device_id,
            (Device.last_seen_at.is_(None) | (Device.last_seen_at < measured_at)),
        )
        .values(last_seen_at=measured_at)
    )


def add_reset_event(
    session: Session,
    *,
    device_id: UUID,
    measured_at: datetime,
    source: str,
) -> None:
    session.add(
        SystemEvent(
            event_at=measured_at,
            event_type="meter.reset",
            entity_type="device",
            entity_id=str(device_id),
            details_json={"source": source},
        )
    )
