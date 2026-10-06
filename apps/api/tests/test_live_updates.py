import asyncio
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from starlette.websockets import WebSocketDisconnect

from app.core.auth import hash_password
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.main import app
from app.models import AuthSession, Device, SystemEvent, User
from app.models.enums import UserRole
from app.services.live import LiveConnectionManager, Subscription

EMAIL = "step9-live@example.com"
PASSWORD = "A-strong-live-password-42!"


@pytest.fixture(scope="module", autouse=True)
def live_user() -> None:
    with get_session_factory()() as session:
        user = User(
            id=uuid4(),
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            role=UserRole.VIEWER,
        )
        session.add(user)
        session.commit()
    yield
    with get_session_factory()() as session:
        user_id = session.scalar(select(User.id).where(User.email == EMAIL))
        if user_id is not None:
            session.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
            session.execute(
                delete(SystemEvent).where(SystemEvent.actor_user_id == user_id)
            )
            session.execute(delete(User).where(User.id == user_id))
            session.commit()


def authenticate(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    assert response.status_code == 200


def test_websocket_rejects_unauthenticated_connection() -> None:
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as caught:
            with client.websocket_connect("/api/v1/ws/live"):
                pass
    assert caught.value.code == 4401


def test_ingested_measurement_arrives_with_sequence_within_two_seconds() -> None:
    with get_session_factory()() as session:
        device = session.scalar(select(Device).order_by(Device.code))
        assert device is not None
        device_id = device.id
        device_code = device.code
    with TestClient(app) as client:
        authenticate(client)
        with client.websocket_connect("/api/v1/ws/live") as websocket:
            websocket.send_json(
                {
                    "type": "subscribe",
                    "device_ids": [str(device_id)],
                    "event_types": ["measurement.new", "device.status"],
                }
            )
            confirmed = websocket.receive_json()
            assert confirmed["type"] == "subscription.confirmed"
            measured_at = datetime.now(UTC)
            response = client.post(
                "/api/v1/ingest/measurements",
                headers={
                    "X-Ingest-Key": get_settings().INGEST_API_KEY.get_secret_value()
                },
                json={
                    "source": "simulator",
                    "records": [
                        {
                            "device_code": device_code,
                            "measured_at": measured_at.isoformat(),
                            "active_power_kw": 4.2,
                            "data_quality": "good",
                        }
                    ],
                },
            )
            assert response.status_code == 202
            started = datetime.now(UTC)
            event = websocket.receive_json()
            while event["type"] == "heartbeat":
                event = websocket.receive_json()
            elapsed = (datetime.now(UTC) - started).total_seconds()
            assert event["type"] == "measurement.new"
            assert event["sequence"] > confirmed["sequence"]
            assert event["payload"]["active_power_kw"] == 4.2
            assert elapsed < 2


class RecordingWebSocket:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def send_json(self, event: dict[str, Any]) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_measurement_updates_are_coalesced_to_one_per_second() -> None:
    manager = LiveConnectionManager()
    websocket = RecordingWebSocket()
    device_id = uuid4()
    manager._connections[cast(WebSocket, websocket)] = Subscription()
    await manager.publish("measurement.new", {"value": 1}, device_id=device_id)
    await manager.publish("measurement.new", {"value": 2}, device_id=device_id)
    await manager.publish("measurement.new", {"value": 3}, device_id=device_id)
    await asyncio.sleep(1.05)
    assert [event["payload"]["value"] for event in websocket.events] == [1, 3]
    first = datetime.fromisoformat(websocket.events[0]["emitted_at"])
    second = datetime.fromisoformat(websocket.events[1]["emitted_at"])
    assert (second - first).total_seconds() >= 0.9
