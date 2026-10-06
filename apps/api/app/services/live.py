"""Authenticated live connection manager with sequencing and coalescing."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import monotonic
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from app.schemas.live import LiveEvent, LiveEventType
from app.services.ingestion import CommittedMeasurement


@dataclass
class Subscription:
    device_ids: set[UUID] = field(default_factory=set)
    event_types: set[LiveEventType] = field(default_factory=set)


class LiveConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[WebSocket, Subscription] = {}
        self._sequence = 0
        self._lock = asyncio.Lock()
        self._last_measurement_at: dict[UUID, float] = {}
        self._pending_measurements: dict[UUID, dict[str, Any]] = {}
        self._flush_tasks: dict[UUID, asyncio.Task[None]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[websocket] = Subscription()

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)

    def subscribe(
        self,
        websocket: WebSocket,
        *,
        device_ids: set[UUID],
        event_types: set[LiveEventType],
    ) -> None:
        self._connections[websocket] = Subscription(device_ids, event_types)

    async def publish(
        self,
        event_type: LiveEventType,
        payload: dict[str, Any],
        *,
        device_id: UUID | None = None,
    ) -> None:
        if event_type == "measurement.new" and device_id is not None:
            elapsed = monotonic() - self._last_measurement_at.get(device_id, -10.0)
            if elapsed < 1.0:
                self._pending_measurements[device_id] = payload
                if device_id not in self._flush_tasks:
                    self._flush_tasks[device_id] = asyncio.create_task(
                        self._flush_measurement(device_id, 1.0 - elapsed)
                    )
                return
            self._last_measurement_at[device_id] = monotonic()
        await self._emit(event_type, payload, device_id=device_id)

    async def _flush_measurement(self, device_id: UUID, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
            payload = self._pending_measurements.pop(device_id, None)
            if payload is not None:
                self._last_measurement_at[device_id] = monotonic()
                await self._emit("measurement.new", payload, device_id=device_id)
        finally:
            self._flush_tasks.pop(device_id, None)

    async def _emit(
        self,
        event_type: LiveEventType,
        payload: dict[str, Any],
        *,
        device_id: UUID | None = None,
    ) -> None:
        async with self._lock:
            self._sequence += 1
            event = LiveEvent(
                type=event_type,
                emitted_at=datetime.now(UTC),
                sequence=self._sequence,
                payload=payload,
            ).model_dump(mode="json")
            failed: list[WebSocket] = []
            for websocket, subscription in list(self._connections.items()):
                event_selected = event_type in {
                    "heartbeat",
                    "subscription.confirmed",
                } or (
                    not subscription.event_types
                    or event_type in subscription.event_types
                )
                device_selected = (
                    device_id is None
                    or not subscription.device_ids
                    or device_id in subscription.device_ids
                )
                if event_selected and device_selected:
                    try:
                        await websocket.send_json(event)
                    except RuntimeError:
                        failed.append(websocket)
            for websocket in failed:
                self.disconnect(websocket)

    async def heartbeat_forever(self) -> None:
        while True:
            await asyncio.sleep(5)
            await self._emit("heartbeat", {})

    async def reset_for_test(self) -> None:
        for task in self._flush_tasks.values():
            task.cancel()
        self._connections.clear()
        self._last_measurement_at.clear()
        self._pending_measurements.clear()
        self._flush_tasks.clear()
        self._sequence = 0


live_manager = LiveConnectionManager()


async def publish_committed_measurements(
    items: list[CommittedMeasurement],
) -> None:
    device_codes: dict[UUID, str] = {}
    for item in items:
        device_codes[item.device_id] = item.device_code
        record = item.record
        await live_manager.publish(
            "measurement.new",
            {
                "device_id": str(item.device_id),
                "device_code": item.device_code,
                "measured_at": record.measured_at.isoformat(),
                "active_power_kw": record.active_power_kw,
                "voltage_v": record.voltage_v,
                "current_a": record.current_a,
                "power_factor": record.power_factor,
                "frequency_hz": record.frequency_hz,
                "data_quality": record.data_quality,
            },
            device_id=item.device_id,
        )
    for device_id, device_code in device_codes.items():
        await live_manager.publish(
            "device.status",
            {
                "device_id": str(device_id),
                "device_code": device_code,
                "status": "online",
            },
            device_id=device_id,
        )
