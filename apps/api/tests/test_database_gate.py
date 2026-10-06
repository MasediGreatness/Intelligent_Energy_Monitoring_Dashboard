"""Step 3 PostgreSQL constraint and readiness gate tests."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.config import get_settings
from app.core.errors import ApplicationError
from app.db.session import get_engine
from app.main import app
from app.services.readiness import check_readiness


def test_duplicate_measurement_is_rejected() -> None:
    engine = create_engine(get_settings().DATABASE_URL)
    device_id = uuid4()
    measured_at = datetime.now(UTC)

    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO devices "
                "(id, code, name, location, phase_type, rated_power_kw, criticality) "
                "VALUES (:id, :code, 'Test load', 'Test bench', "
                "'single_phase', 1.0, 'low')"
            ),
            {"id": device_id, "code": f"TEST-{device_id}"},
        )
        record = {
            "device_id": device_id,
            "measured_at": measured_at,
        }
        statement = text(
            "INSERT INTO measurements "
            "(device_id, measured_at, active_power_kw, data_quality) "
            "VALUES (:device_id, :measured_at, 1.0, 'good')"
        )
        connection.execute(statement, record)
        connection.execute(statement, record)


def test_invalid_role_enum_is_rejected() -> None:
    engine = create_engine(get_settings().DATABASE_URL)
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, role) "
                "VALUES (:id, :email, 'not-a-real-hash', 'owner')"
            ),
            {"id": uuid4(), "email": f"invalid-{uuid4()}@example.invalid"},
        )


def test_ready_reports_migration_without_credentials() -> None:
    get_engine.cache_clear()
    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ready",
        "migrations": "at_head",
        "revision": "0003",
    }
    assert "postgresql" not in response.text
    assert "energy" not in response.text


def test_unavailable_database_returns_safe_readiness_error() -> None:
    unavailable = create_engine(
        "postgresql+psycopg://energy:@127.0.0.1:1/energy?connect_timeout=1"
    )
    with pytest.raises(ApplicationError) as captured:
        check_readiness(unavailable)

    assert captured.value.status_code == 503
    assert captured.value.code == "DATABASE_NOT_READY"
    assert "postgresql" not in captured.value.message
