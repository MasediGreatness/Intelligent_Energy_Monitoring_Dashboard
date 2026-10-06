from datetime import UTC, date, datetime, timedelta
from time import perf_counter

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from openapi_spec_validator import validate
from sqlalchemy import select

from app.core.auth import current_user
from app.db.session import get_session_factory
from app.main import app
from app.models import Device, User
from app.models.enums import UserRole


def read_test_user() -> User:
    return User(
        email="read-tests@example.com",
        password_hash="not-used",
        role=UserRole.VIEWER,
    )


def setup_module() -> None:
    app.dependency_overrides[current_user] = read_test_user


def teardown_module() -> None:
    app.dependency_overrides.pop(current_user, None)


def test_all_read_endpoints_and_pagination_contract() -> None:
    with get_session_factory()() as session:
        device_id = session.scalar(select(Device.id).order_by(Device.code))
    assert device_id is not None
    now = datetime.now(UTC)
    today = date.today().isoformat()
    history_params = [
        ("device_id", str(device_id)),
        ("from", (now - timedelta(hours=1)).isoformat()),
        ("to", now.isoformat()),
        ("interval", "1m"),
        ("metric", "active_power_kw"),
        ("timezone", "Africa/Johannesburg"),
    ]
    requests = [
        ("/api/v1/dashboard/summary", {}),
        ("/api/v1/measurements/latest", {}),
        ("/api/v1/measurements/history", history_params),
        (
            "/api/v1/energy/daily",
            {"from_date": today, "to_date": today, "device_id": str(device_id)},
        ),
        ("/api/v1/forecasts/latest", {"horizon_minutes": 60}),
        ("/api/v1/anomalies", {"page": 1, "page_size": 10}),
        ("/api/v1/alarms", {"page": 1, "page_size": 10}),
        ("/api/v1/devices", {"page": 1, "page_size": 10}),
        ("/api/v1/settings", {}),
        ("/api/v1/events", {"page": 1, "page_size": 10}),
    ]
    with TestClient(app) as client:
        for path, params in requests:
            response = client.get(path, params=params)
            assert response.status_code == 200, (path, response.text)
        paged_paths = (
            "/api/v1/anomalies",
            "/api/v1/alarms",
            "/api/v1/devices",
            "/api/v1/events",
        )
        for path in paged_paths:
            body = client.get(path).json()
            assert set(("page", "page_size", "total", "items")) <= body.keys()


def test_openapi_validates_and_every_api_route_has_a_response_model() -> None:
    schema = app.openapi()
    validate(schema)
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api/v1"):
            assert route.response_model is not None, route.path


def test_history_24_hours_at_one_minute_is_under_two_seconds() -> None:
    with get_session_factory()() as session:
        device_id = session.scalar(select(Device.id).order_by(Device.code))
    assert device_id is not None
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    with TestClient(app) as client:
        started = perf_counter()
        response = client.get(
            "/api/v1/measurements/history",
            params=[
                ("device_id", str(device_id)),
                ("from", (now - timedelta(hours=24)).isoformat()),
                ("to", now.isoformat()),
                ("interval", "1m"),
                ("metric", "active_power_kw"),
                ("timezone", "UTC"),
            ],
        )
        elapsed = perf_counter() - started
    assert response.status_code == 200
    assert len(response.json()["series"][0]["points"]) == 1440
    assert elapsed < 2, f"24-hour history took {elapsed:.3f}s"


def test_history_errors_use_standard_envelope() -> None:
    now = datetime.now(UTC)
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/measurements/history",
            params=[
                ("device_id", "00000000-0000-0000-0000-000000000001"),
                ("from", now.isoformat()),
                ("to", (now - timedelta(hours=1)).isoformat()),
                ("interval", "1m"),
                ("metric", "active_power_kw"),
            ],
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_query_validation_uses_standard_envelope() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/devices", params={"page_size": 201})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"] == {"field": "page_size"}
