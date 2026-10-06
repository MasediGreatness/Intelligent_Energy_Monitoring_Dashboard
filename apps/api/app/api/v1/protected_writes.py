"""Role-protected mutations with append-only audit records."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from anyio import from_thread
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.errors import ApplicationError
from app.db.session import get_db_session
from app.models import Alarm, Device, Setting, User
from app.models.enums import LifecycleStatus, UserRole
from app.schemas.read import AlarmItem, DeviceItem, SettingItem
from app.schemas.write import (
    AlarmAcknowledgeRequest,
    AlarmAcknowledgeResponse,
    DeviceCreateRequest,
    DeviceMutationResponse,
    DeviceUpdateRequest,
    SettingUpdateRequest,
    SettingUpdateResponse,
)
from app.services.audit import record_audit_event
from app.services.calculations import device_status
from app.services.live import live_manager
from app.services.settings import SETTING_DEFAULTS, validate_setting_value


async def _publish_alarm_changed(alarm: Alarm) -> None:
    await live_manager.publish(
        "alarm.changed",
        {
            "alarm_id": str(alarm.id),
            "device_id": str(alarm.device_id) if alarm.device_id else None,
            "status": alarm.status.value,
            "severity": alarm.severity.value,
            "acknowledged_at": (
                alarm.acknowledged_at.isoformat() if alarm.acknowledged_at else None
            ),
        },
        device_id=alarm.device_id,
    )


async def _publish_device_changed(device: Device) -> None:
    await live_manager.publish(
        "device.status",
        {"device_id": str(device.id), "enabled": device.enabled},
        device_id=device.id,
    )


def _device_item(session: Session, device: Device) -> DeviceItem:
    timeout_values = {
        row.key: row.value_json
        for row in session.scalars(
            select(Setting).where(
                Setting.key.in_(["online_timeout_seconds", "stale_timeout_seconds"])
            )
        )
    }
    online_timeout = timeout_values.get("online_timeout_seconds", 10)
    stale_timeout = timeout_values.get("stale_timeout_seconds", 60)
    return DeviceItem(
        id=device.id,
        code=device.code,
        name=device.name,
        location=device.location,
        phase_type=device.phase_type,
        rated_power_kw=device.rated_power_kw,
        criticality=device.criticality,
        enabled=device.enabled,
        last_seen_at=device.last_seen_at,
        status=device_status(
            enabled=device.enabled,
            latest_at=device.last_seen_at,
            now=datetime.now(UTC),
            online_timeout_seconds=(
                online_timeout if isinstance(online_timeout, int) else 10
            ),
            stale_timeout_seconds=(
                stale_timeout if isinstance(stale_timeout, int) else 60
            ),
        ),
    )


router = APIRouter(prefix="/api/v1", tags=["protected writes"])
Operator = Annotated[User, Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN))]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
DbSession = Annotated[Session, Depends(get_db_session)]


@router.patch("/alarms/{alarm_id}/acknowledge", response_model=AlarmAcknowledgeResponse)
def acknowledge_alarm(
    alarm_id: UUID,
    body: AlarmAcknowledgeRequest,
    session: DbSession,
    user: Operator,
) -> AlarmAcknowledgeResponse:
    alarm = session.get(Alarm, alarm_id)
    if alarm is None:
        raise ApplicationError(
            status_code=404, code="ALARM_NOT_FOUND", message="Alarm not found."
        )
    if alarm.status == LifecycleStatus.CLEARED:
        raise ApplicationError(
            status_code=409,
            code="ALARM_ALREADY_CLEARED",
            message="A cleared alarm cannot be acknowledged.",
        )
    if alarm.status == LifecycleStatus.ACKNOWLEDGED:
        raise ApplicationError(
            status_code=409,
            code="ALARM_ALREADY_ACKNOWLEDGED",
            message="The alarm has already been acknowledged.",
        )
    alarm.status = LifecycleStatus.ACKNOWLEDGED
    alarm.acknowledged_at = datetime.now(UTC)
    alarm.acknowledged_by = user.id
    alarm.acknowledgement_note = body.note
    record_audit_event(
        session,
        event_type="alarm.acknowledged",
        actor_user_id=user.id,
        entity_type="alarm",
        entity_id=str(alarm.id),
        details={"note": body.note},
    )
    session.commit()
    session.refresh(alarm)
    from_thread.run(_publish_alarm_changed, alarm)
    return AlarmAcknowledgeResponse(alarm=AlarmItem.model_validate(alarm))


@router.post("/devices", response_model=DeviceMutationResponse, status_code=201)
def create_device(
    body: DeviceCreateRequest,
    session: DbSession,
    user: Admin,
) -> DeviceMutationResponse:
    if session.scalar(select(Device.id).where(Device.code == body.code)) is not None:
        raise ApplicationError(
            status_code=409,
            code="DEVICE_CODE_EXISTS",
            message="A device with this code already exists.",
            details={"field": "code"},
        )
    values = body.model_dump()
    device = Device(**values)
    session.add(device)
    session.flush()
    record_audit_event(
        session,
        event_type="device.created",
        actor_user_id=user.id,
        entity_type="device",
        entity_id=str(device.id),
        details={"code": device.code},
    )
    session.commit()
    session.refresh(device)
    from_thread.run(_publish_device_changed, device)
    return DeviceMutationResponse(device=_device_item(session, device))


@router.patch("/devices/{device_id}", response_model=DeviceMutationResponse)
def update_device(
    device_id: UUID,
    body: DeviceUpdateRequest,
    session: DbSession,
    user: Admin,
) -> DeviceMutationResponse:
    device = session.get(Device, device_id)
    if device is None:
        raise ApplicationError(
            status_code=404, code="DEVICE_NOT_FOUND", message="Device not found."
        )
    changes = body.model_dump(exclude_unset=True)
    code = changes.get("code")
    if (
        code is not None
        and session.scalar(
            select(Device.id).where(Device.code == code, Device.id != device_id)
        )
        is not None
    ):
        raise ApplicationError(
            status_code=409,
            code="DEVICE_CODE_EXISTS",
            message="A device with this code already exists.",
            details={"field": "code"},
        )
    previous = {field: getattr(device, field) for field in changes}
    for field, value in changes.items():
        setattr(device, field, value)
    audit_changes = {
        field: {
            "from": value.value if hasattr(value, "value") else value,
            "to": (
                changes[field].value
                if hasattr(changes[field], "value")
                else changes[field]
            ),
        }
        for field, value in previous.items()
    }
    record_audit_event(
        session,
        event_type="device.updated",
        actor_user_id=user.id,
        entity_type="device",
        entity_id=str(device.id),
        details={"changes": audit_changes},
    )
    session.commit()
    session.refresh(device)
    from_thread.run(_publish_device_changed, device)
    return DeviceMutationResponse(device=_device_item(session, device))


@router.patch("/settings/{key}", response_model=SettingUpdateResponse)
def update_setting(
    key: str,
    body: SettingUpdateRequest,
    session: DbSession,
    user: Admin,
) -> SettingUpdateResponse:
    setting = session.get(Setting, key)
    if setting is None:
        raise ApplicationError(
            status_code=404, code="SETTING_NOT_FOUND", message="Setting not found."
        )
    current_values = SETTING_DEFAULTS | {
        row.key: row.value_json for row in session.scalars(select(Setting))
    }
    previous = setting.value_json
    setting.value_json = validate_setting_value(key, body.value, current_values)
    setting.updated_by = user.id
    setting.updated_at = datetime.now(UTC)
    record_audit_event(
        session,
        event_type="setting.updated",
        actor_user_id=user.id,
        entity_type="setting",
        entity_id=key,
        details={"from": previous, "to": setting.value_json},
    )
    session.commit()
    session.refresh(setting)
    return SettingUpdateResponse(setting=SettingItem.model_validate(setting))
