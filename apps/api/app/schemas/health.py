"""Health endpoint schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Process-only liveness response."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: Literal["energy-dashboard-api"]
    version: str
