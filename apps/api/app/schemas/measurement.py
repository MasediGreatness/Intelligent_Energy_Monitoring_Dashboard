"""Stable measurement contract shared by simulator and future gateway ingestion."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeasurementRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_code: str
    measured_at: datetime
    voltage_v: float | None = Field(default=None, ge=0, le=1000)
    current_a: float | None = Field(default=None, ge=0, le=2000)
    active_power_kw: float | None = Field(default=None, ge=-2000, le=2000)
    reactive_power_kvar: float | None = None
    apparent_power_kva: float | None = None
    power_factor: float | None = Field(default=None, ge=0, le=1)
    frequency_hz: float | None = Field(default=None, ge=40, le=70)
    energy_kwh_total: Decimal | None = Field(default=None, ge=0)
    data_quality: Literal["good", "suspect", "missing"]

    @field_validator("measured_at")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("measured_at must be timezone-aware")
        return value
