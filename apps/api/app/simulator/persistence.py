"""Idempotent persistence for deterministic simulator outputs."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Anomaly, Device, Forecast, Measurement, SystemEvent
from app.models.enums import Criticality, PhaseType
from app.simulator.catalog import DEVICES
from app.simulator.generator import SimulationResult


def seed_devices(session: Session) -> int:
    for item in DEVICES:
        statement = (
            insert(Device)
            .values(
                id=item.id,
                code=item.code,
                name=item.name,
                location=item.location,
                phase_type=PhaseType(item.phase_type),
                rated_power_kw=item.rated_power_kw,
                criticality=Criticality(item.criticality),
                enabled=True,
            )
            .on_conflict_do_update(
                index_elements=[Device.code],
                set_={
                    "name": item.name,
                    "location": item.location,
                    "phase_type": PhaseType(item.phase_type),
                    "rated_power_kw": item.rated_power_kw,
                    "criticality": Criticality(item.criticality),
                    "enabled": True,
                },
            )
        )
        session.execute(statement)
    session.commit()
    return len(DEVICES)


def persist_simulation(session: Session, result: SimulationResult) -> dict[str, int]:
    device_ids: dict[str, UUID] = {
        code: device_id
        for code, device_id in session.execute(select(Device.code, Device.id))
    }
    measurement_rows = [
        dict(
            record.model_dump(exclude={"device_code"}),
            device_id=device_ids[record.device_code],
        )
        for record in result.measurements
    ]
    if measurement_rows:
        statement = (
            insert(Measurement)
            .values(measurement_rows)
            .on_conflict_do_nothing(constraint="uq_measurements_device_measured_at")
        )
        inserted = len(
            session.execute(statement.returning(Measurement.id)).scalars().all()
        )
    else:
        inserted = 0
    for forecast in result.forecasts:
        session.execute(
            delete(Forecast).where(
                Forecast.generated_at == forecast.generated_at,
                Forecast.target_at == forecast.target_at,
                Forecast.model_version == forecast.model_version,
            )
        )
        session.add(Forecast(**forecast.model_dump()))
    for anomaly in result.anomalies:
        session.merge(Anomaly(**anomaly.model_dump()))
    events_written = 0
    for event in result.events:
        exists = session.scalar(
            select(SystemEvent.id).where(
                SystemEvent.event_at == event.event_at,
                SystemEvent.event_type == event.event_type,
                SystemEvent.entity_id == event.entity_id,
            )
        )
        if exists is None:
            session.add(
                SystemEvent(
                    event_at=event.event_at,
                    event_type=event.event_type,
                    entity_type="device",
                    entity_id=event.entity_id,
                    details_json=event.details,
                )
            )
            events_written += 1
    session.commit()
    return {
        "measurements_inserted": inserted,
        "forecasts_written": len(result.forecasts),
        "anomalies_written": len(result.anomalies),
        "events_written": events_written,
    }
