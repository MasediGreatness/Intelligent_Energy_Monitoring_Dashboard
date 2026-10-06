"""Authenticated live WebSocket endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.auth import SESSION_COOKIE_NAME, authenticate_token
from app.core.errors import ApplicationError
from app.db.session import get_db_session
from app.schemas.live import LiveSubscription
from app.services.live import live_manager

router = APIRouter(prefix="/api/v1", tags=["live updates"])


@router.websocket("/ws/live")
async def live_updates(
    websocket: WebSocket,
    session: Annotated[Session, Depends(get_db_session)],
) -> None:
    try:
        authenticate_token(session, websocket.cookies.get(SESSION_COOKIE_NAME))
    except ApplicationError:
        await websocket.close(code=4401, reason="Authentication required")
        return
    await live_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_json()
            try:
                message = LiveSubscription.model_validate(raw)
            except ValidationError:
                await websocket.close(code=4400, reason="Invalid subscription")
                return
            live_manager.subscribe(
                websocket,
                device_ids=set(message.device_ids),
                event_types=set(message.event_types),
            )
            await live_manager.publish(
                "subscription.confirmed",
                {
                    "device_ids": [str(item) for item in message.device_ids],
                    "event_types": message.event_types,
                },
            )
    except WebSocketDisconnect:
        live_manager.disconnect(websocket)
