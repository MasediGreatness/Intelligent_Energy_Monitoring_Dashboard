"""Append-only security and configuration audit recording."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import SystemEvent


def record_audit_event(
    session: Session,
    *,
    event_type: str,
    actor_user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    session.add(
        SystemEvent(
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details or {},
        )
    )
