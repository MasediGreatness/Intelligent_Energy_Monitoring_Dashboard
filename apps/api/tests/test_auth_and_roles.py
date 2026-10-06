from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.cli.create_user import normalize_email
from app.core.auth import hash_password
from app.core.config import Settings
from app.core.rate_limit import limiter
from app.db.session import get_session_factory
from app.main import app
from app.models import Alarm, AuthSession, Device, Setting, SystemEvent, User
from app.models.enums import LifecycleStatus, Severity, UserRole

PASSWORD = "A-strong-test-password-42!"
EMAILS = {
    UserRole.VIEWER: "step8-viewer@example.com",
    UserRole.OPERATOR: "step8-operator@example.com",
    UserRole.ADMIN: "step8-admin@example.com",
}
SETTING_KEY = "tariff_zar_per_kwh"


@pytest.fixture(autouse=True)
def reset_login_rate_limit() -> None:
    limiter.reset()


@pytest.fixture(scope="module", autouse=True)
def security_records() -> None:
    with get_session_factory()() as session:
        users = [
            User(
                id=uuid4(),
                email=email,
                password_hash=hash_password(PASSWORD),
                role=role,
            )
            for role, email in EMAILS.items()
        ]
        session.add_all(users)
        setting = session.get(Setting, SETTING_KEY)
        assert setting is not None
        original_setting = (
            setting.value_json,
            setting.updated_at,
            setting.updated_by,
        )
        session.commit()
    yield
    with get_session_factory()() as session:
        user_ids = list(
            session.scalars(select(User.id).where(User.email.in_(EMAILS.values())))
        )
        session.execute(delete(AuthSession).where(AuthSession.user_id.in_(user_ids)))
        session.execute(
            delete(SystemEvent).where(SystemEvent.actor_user_id.in_(user_ids))
        )
        session.execute(delete(SystemEvent).where(SystemEvent.entity_id == SETTING_KEY))
        setting = session.get(Setting, SETTING_KEY)
        assert setting is not None
        setting.value_json, setting.updated_at, setting.updated_by = original_setting
        session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def login(client: TestClient, role: UserRole) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAILS[role], "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    assert response.json()["user"]["role"] == role.value
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Secure" not in response.headers["set-cookie"]
    assert PASSWORD not in response.text


def create_alarm() -> str:
    with get_session_factory()() as session:
        device_id = session.scalar(select(Device.id).order_by(Device.code))
        assert device_id is not None
        alarm = Alarm(
            id=uuid4(),
            device_id=device_id,
            source="step8-test",
            alarm_type="role_test",
            severity=Severity.LOW,
            message="Temporary role test alarm",
            triggered_at=datetime.now(UTC),
            status=LifecycleStatus.OPEN,
        )
        session.add(alarm)
        session.commit()
        return str(alarm.id)


def delete_alarm(alarm_id: str) -> None:
    with get_session_factory()() as session:
        session.execute(delete(SystemEvent).where(SystemEvent.entity_id == alarm_id))
        session.execute(delete(Alarm).where(Alarm.id == alarm_id))
        session.commit()


def test_password_is_argon2_hashed() -> None:
    value = hash_password(PASSWORD)
    assert value.startswith("$argon2")
    assert PASSWORD not in value


def test_setup_email_uses_the_login_validation_contract() -> None:
    assert normalize_email(" ADMIN@EXAMPLE.COM ") == "admin@example.com"
    with pytest.raises(SystemExit, match="valid address"):
        normalize_email("admin@example.test")


def test_openapi_declares_http_only_session_cookie_scheme() -> None:
    schemes = app.openapi()["components"]["securitySchemes"]
    assert schemes["APIKeyCookie"]["in"] == "cookie"
    assert schemes["APIKeyCookie"]["name"] == "energy_session"


def test_login_cookie_security_follows_explicit_tls_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "DATABASE_URL": "postgresql+psycopg://energy:@db:5432/energy",
        "APP_SECRET_KEY": "a" * 32,
        "INGEST_API_KEY": "b" * 24,
        "SESSION_COOKIE_SECURE": True,
    }
    settings = Settings(**config)  # type: ignore[arg-type]
    monkeypatch.setattr("app.api.v1.auth.get_settings", lambda: settings)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": EMAILS[UserRole.VIEWER],
                "password": PASSWORD,
            },
        )

    assert response.status_code == 200
    assert "Secure" in response.headers["set-cookie"]


def test_unauthenticated_calls_return_standard_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")
        read_response = client.get("/api/v1/devices")
        protected = client.patch(f"/api/v1/settings/{SETTING_KEY}", json={"value": 2})
    assert response.status_code == 401
    assert read_response.status_code == 401
    assert protected.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_viewer_cannot_acknowledge_alarm() -> None:
    alarm_id = create_alarm()
    try:
        with TestClient(app) as client:
            login(client, UserRole.VIEWER)
            response = client.patch(
                f"/api/v1/alarms/{alarm_id}/acknowledge",
                json={"note": "Viewer must be rejected"},
            )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"
    finally:
        delete_alarm(alarm_id)


def test_acknowledgement_note_cannot_be_blank() -> None:
    alarm_id = create_alarm()
    try:
        with TestClient(app) as client:
            login(client, UserRole.OPERATOR)
            response = client.patch(
                f"/api/v1/alarms/{alarm_id}/acknowledge", json={"note": "   "}
            )
        assert response.status_code == 422
        with get_session_factory()() as session:
            alarm = session.get(Alarm, alarm_id)
            assert alarm is not None
            assert alarm.status == LifecycleStatus.OPEN
            assert alarm.acknowledged_by is None
    finally:
        delete_alarm(alarm_id)


def test_operator_can_acknowledge_but_cannot_edit_settings() -> None:
    alarm_id = create_alarm()
    try:
        with TestClient(app) as client:
            login(client, UserRole.OPERATOR)
            acknowledged = client.patch(
                f"/api/v1/alarms/{alarm_id}/acknowledge",
                json={"note": "Checked by operator"},
            )
            setting = client.patch(f"/api/v1/settings/{SETTING_KEY}", json={"value": 3})
        assert acknowledged.status_code == 200
        alarm_body = acknowledged.json()["alarm"]
        assert alarm_body["status"] == "acknowledged"
        assert alarm_body["acknowledged_at"] is not None
        assert alarm_body["acknowledgement_note"] == "Checked by operator"
        assert setting.status_code == 403
        with get_session_factory()() as session:
            operator_id = session.scalar(
                select(User.id).where(User.email == EMAILS[UserRole.OPERATOR])
            )
            audit = session.scalar(
                select(SystemEvent).where(SystemEvent.entity_id == alarm_id)
            )
        assert operator_id is not None
        assert alarm_body["acknowledged_by"] == str(operator_id)
        assert audit is not None
        assert audit.event_type == "alarm.acknowledged"
        assert audit.actor_user_id == operator_id
        assert audit.event_at is not None
    finally:
        delete_alarm(alarm_id)


def test_admin_edits_setting_and_audit_events_exist() -> None:
    with TestClient(app) as client:
        failed = client.post(
            "/api/v1/auth/login",
            json={"email": EMAILS[UserRole.ADMIN], "password": "wrong-password"},
        )
        login(client, UserRole.ADMIN)
        response = client.patch(f"/api/v1/settings/{SETTING_KEY}", json={"value": 7})
    assert failed.status_code == 401
    assert response.status_code == 200
    with get_session_factory()() as session:
        event_types = set(
            session.scalars(
                select(SystemEvent.event_type).where(
                    SystemEvent.event_type.in_(["auth.login_failed", "setting.updated"])
                )
            )
        )
    assert event_types == {"auth.login_failed", "setting.updated"}


def test_invalid_operational_settings_are_rejected_without_mutation() -> None:
    with TestClient(app) as client:
        login(client, UserRole.ADMIN)
        before = client.get("/api/v1/settings").json()
        demand_before = next(
            item["value_json"] for item in before if item["key"] == "demand_limit_kw"
        )
        invalid_limit = client.patch(
            "/api/v1/settings/demand_limit_kw", json={"value": -1}
        )
        invalid_timeouts = client.patch(
            "/api/v1/settings/stale_timeout_seconds", json={"value": 5}
        )
        after = client.get("/api/v1/settings").json()
    assert invalid_limit.status_code == 422
    assert invalid_limit.json()["error"]["code"] == "INVALID_SETTING_VALUE"
    assert invalid_timeouts.status_code == 422
    assert invalid_timeouts.json()["error"]["code"] == "INVALID_SETTING_VALUE"
    assert (
        next(item["value_json"] for item in after if item["key"] == "demand_limit_kw")
        == demand_before
    )


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.OPERATOR])
def test_non_admin_cannot_create_or_update_devices(role: UserRole) -> None:
    with get_session_factory()() as session:
        device_id = session.scalar(select(Device.id).order_by(Device.code))
    assert device_id is not None
    with TestClient(app) as client:
        login(client, role)
        created = client.post(
            "/api/v1/devices",
            json={
                "code": f"DENIED-{role.value.upper()}",
                "name": "Denied device",
                "location": "Test bench",
                "phase_type": "single_phase",
                "rated_power_kw": 2,
                "criticality": "low",
                "enabled": True,
            },
        )
        updated = client.patch(f"/api/v1/devices/{device_id}", json={"enabled": False})
    assert created.status_code == 403
    assert updated.status_code == 403


def test_admin_can_create_edit_and_disable_but_not_delete_device() -> None:
    code = f"STEP13-{str(uuid4())[:8].upper()}"
    device_id: str | None = None
    try:
        with TestClient(app) as client:
            login(client, UserRole.ADMIN)
            created = client.post(
                "/api/v1/devices",
                json={
                    "code": code,
                    "name": "Step 13 temporary load",
                    "location": "Test bench",
                    "phase_type": "three_phase",
                    "rated_power_kw": 12.5,
                    "criticality": "high",
                    "enabled": True,
                },
            )
            assert created.status_code == 201, created.text
            device_id = created.json()["device"]["id"]
            updated = client.patch(
                f"/api/v1/devices/{device_id}",
                json={"name": "Updated Step 13 load", "enabled": False},
            )
            deleted = client.delete(f"/api/v1/devices/{device_id}")
        assert updated.status_code == 200
        assert updated.json()["device"]["enabled"] is False
        assert updated.json()["device"]["status"] == "disabled"
        assert deleted.status_code == 405
        with get_session_factory()() as session:
            events = set(
                session.scalars(
                    select(SystemEvent.event_type).where(
                        SystemEvent.entity_id == device_id
                    )
                )
            )
        assert events == {"device.created", "device.updated"}
    finally:
        if device_id is not None:
            with get_session_factory()() as session:
                session.execute(
                    delete(SystemEvent).where(SystemEvent.entity_id == device_id)
                )
                session.execute(delete(Device).where(Device.id == device_id))
                session.commit()


def test_session_expiry_and_logout_invalidate_cookie() -> None:
    with TestClient(app) as client:
        login(client, UserRole.VIEWER)
        token = client.cookies.get("energy_session")
        assert token is not None
        with get_session_factory()() as session:
            auth_session = session.scalar(
                select(AuthSession).order_by(AuthSession.created_at.desc())
            )
            assert auth_session is not None
            auth_session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            session.commit()
        assert client.get("/api/v1/auth/me").status_code == 401

    with TestClient(app) as client:
        login(client, UserRole.VIEWER)
        assert client.post("/api/v1/auth/logout").status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401


def test_logs_do_not_contain_password_or_session_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with TestClient(app) as client:
        login(client, UserRole.VIEWER)
        token = client.cookies.get("energy_session")
    log_text = caplog.text
    assert PASSWORD not in log_text
    assert token is not None
    assert token not in log_text
