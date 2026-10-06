from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnomalyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    device_id: UUID
    detected_at: datetime
    anomaly_type: str
    severity: Literal["low", "medium", "high", "critical"]
    metric: str
    actual_value: float | None
    expected_value: float | None
    score: float
    explanation: str
    status: Literal["open", "reviewed", "cleared"] = "open"
