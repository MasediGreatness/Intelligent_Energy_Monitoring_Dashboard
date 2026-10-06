"""Contracts for the sequenced live-update protocol."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

LiveEventType = Literal[
    "measurement.new",
    "alarm.changed",
    "device.status",
    "heartbeat",
    "subscription.confirmed",
]


class LiveSubscription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["subscribe"]
    device_ids: list[UUID] = Field(default_factory=list, max_length=200)
    event_types: list[LiveEventType] = Field(default_factory=list, max_length=5)


class LiveEvent(BaseModel):
    type: LiveEventType
    emitted_at: datetime
    sequence: int = Field(ge=1)
    payload: dict[str, Any]
