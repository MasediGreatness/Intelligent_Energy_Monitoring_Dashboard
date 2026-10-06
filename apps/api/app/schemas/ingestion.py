"""Measurement ingestion request and response contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.measurement import MeasurementRecord


class MeasurementIngestRecord(MeasurementRecord):
    """Gateway record plus explicit transport-only reset metadata."""

    energy_reset: bool = False

    @model_validator(mode="after")
    def require_frequency_quality(self) -> "MeasurementIngestRecord":
        if (
            self.frequency_hz is not None
            and not 45 <= self.frequency_hz <= 55
            and self.data_quality != "suspect"
        ):
            raise ValueError("frequency outside 45-55 Hz requires data_quality=suspect")
        return self


class MeasurementIngestBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["simulator", "gateway"]
    records: list[dict[str, Any]] = Field(min_length=1, max_length=60)


class IngestionError(BaseModel):
    record_index: int
    field: str
    reason: str


class MeasurementIngestResponse(BaseModel):
    accepted_count: int
    duplicate_count: int
    rejected_count: int
    errors: list[IngestionError]


class ValidatedMeasurement(BaseModel):
    """Internal association that preserves input position."""

    index: int
    record: MeasurementIngestRecord
    received_at: datetime
