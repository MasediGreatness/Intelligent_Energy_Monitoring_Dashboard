from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ForecastRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: UUID | None = None
    generated_at: datetime
    target_at: datetime
    horizon_minutes: int = Field(gt=0)
    predicted_power_kw: float
    lower_kw: float | None = None
    upper_kw: float | None = None
    model_version: str
