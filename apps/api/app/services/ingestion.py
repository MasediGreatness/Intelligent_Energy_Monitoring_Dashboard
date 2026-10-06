"""Validation and idempotent measurement ingestion."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.repositories.measurements import (
    add_reset_event,
    device_ids_by_code,
    insert_measurement,
    latest_energy_counter,
    update_last_seen,
)
from app.schemas.ingestion import (
    IngestionError,
    MeasurementIngestBatch,
    MeasurementIngestRecord,
    MeasurementIngestResponse,
)


@dataclass(frozen=True)
class CommittedMeasurement:
    device_id: UUID
    device_code: str
    record: MeasurementIngestRecord


def _validation_errors(index: int, error: ValidationError) -> list[IngestionError]:
    output: list[IngestionError] = []
    for item in error.errors(include_url=False):
        location = item.get("loc", ())
        field = str(location[-1]) if location else "record"
        output.append(
            IngestionError(
                record_index=index,
                field=field,
                reason=str(item["msg"]),
            )
        )
    return output


def ingest_measurements(
    session: Session,
    batch: MeasurementIngestBatch,
    *,
    now: datetime | None = None,
    on_committed: Callable[[list[CommittedMeasurement]], None] | None = None,
) -> MeasurementIngestResponse:
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    parsed: list[tuple[int, MeasurementIngestRecord]] = []
    errors: list[IngestionError] = []

    for index, raw_record in enumerate(batch.records):
        try:
            record = MeasurementIngestRecord.model_validate(raw_record)
        except ValidationError as exc:
            errors.extend(_validation_errors(index, exc))
            continue
        if record.measured_at.astimezone(UTC) > current_time + timedelta(minutes=5):
            errors.append(
                IngestionError(
                    record_index=index,
                    field="measured_at",
                    reason="timestamp must not be more than 5 minutes in the future",
                )
            )
            continue
        parsed.append((index, record))

    known_devices = device_ids_by_code(
        session, {record.device_code for _, record in parsed}
    )
    accepted = 0
    duplicates = 0
    counters: dict[str, Decimal | None] = {}
    committed: list[CommittedMeasurement] = []

    for index, record in parsed:
        device_id = known_devices.get(record.device_code)
        if device_id is None:
            errors.append(
                IngestionError(
                    record_index=index,
                    field="device_code",
                    reason="unknown device code",
                )
            )
            continue

        previous = counters.get(record.device_code)
        if previous is None:
            previous = latest_energy_counter(session, device_id)
        counter = record.energy_kwh_total
        if counter is not None and previous is not None and counter < previous:
            if not record.energy_reset:
                errors.append(
                    IngestionError(
                        record_index=index,
                        field="energy_kwh_total",
                        reason="counter decrease requires energy_reset=true",
                    )
                )
                continue

        inserted = insert_measurement(session, device_id, record)
        if inserted:
            accepted += 1
            update_last_seen(session, device_id, record.measured_at)
            if record.energy_reset:
                add_reset_event(
                    session,
                    device_id=device_id,
                    measured_at=record.measured_at,
                    source=batch.source,
                )
            if counter is not None:
                counters[record.device_code] = counter
            committed.append(
                CommittedMeasurement(
                    device_id=device_id,
                    device_code=record.device_code,
                    record=record,
                )
            )
        else:
            duplicates += 1

    session.commit()
    if on_committed is not None and committed:
        on_committed(committed)
    rejected_indices = {error.record_index for error in errors}
    return MeasurementIngestResponse(
        accepted_count=accepted,
        duplicate_count=duplicates,
        rejected_count=len(rejected_indices),
        errors=errors,
    )
