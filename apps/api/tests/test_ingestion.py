"""Step 5 ingestion contract and performance tests."""

from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_engine
from app.main import app


def record(*, index: int = 0, **overrides: object) -> dict[str, object]:
    measured_at = datetime.now(UTC) - timedelta(seconds=120 - index)
    payload: dict[str, object] = {
        "device_code": "LOAD-001",
        "measured_at": measured_at.isoformat().replace("+00:00", "Z"),
        "voltage_v": 231.4,
        "current_a": 12.63,
        "active_power_kw": 2.71,
        "reactive_power_kvar": 0.74,
        "apparent_power_kva": 2.81,
        "power_factor": 0.96,
        "frequency_hz": 49.99,
        "energy_kwh_total": 100_000_000_000
        + datetime.now(UTC).timestamp() * 10
        + index,
        "data_quality": "good",
    }
    payload.update(overrides)
    return payload


def headers() -> dict[str, str]:
    return {"X-Ingest-Key": get_settings().INGEST_API_KEY.get_secret_value()}


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_ingestion_device_history() -> None:
    """Keep contract cases independent while preserving other seeded test data."""

    with get_engine().begin() as connection:
        connection.execute(
            text(
                "DELETE FROM measurements WHERE device_id = "
                "(SELECT id FROM devices WHERE code = 'LOAD-001')"
            )
        )


@pytest.fixture(autouse=True)
def reset_ingestion_rate_limit() -> None:
    limiter.reset()


def test_valid_then_duplicate_record(client: TestClient) -> None:
    payload = {"source": "gateway", "records": [record()]}
    first = client.post("/api/v1/ingest/measurements", json=payload, headers=headers())
    second = client.post("/api/v1/ingest/measurements", json=payload, headers=headers())
    assert first.status_code == 202
    assert first.json()["accepted_count"] == 1
    assert second.status_code == 202
    assert second.json()["duplicate_count"] == 1


def test_partial_invalid_does_not_reject_valid_record(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ingest/measurements",
        json={
            "source": "gateway",
            "records": [record(index=1), record(index=2, voltage_v=1001)],
        },
        headers=headers(),
    )
    assert response.status_code == 202
    assert response.json()["accepted_count"] == 1
    assert response.json()["rejected_count"] == 1
    assert response.json()["errors"][0]["record_index"] == 1
    assert response.json()["errors"][0]["field"] == "voltage_v"


def test_unknown_device_is_reported_per_record(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ingest/measurements",
        json={
            "source": "gateway",
            "records": [record(index=3, device_code=f"UNKNOWN-{uuid4()}")],
        },
        headers=headers(),
    )
    assert response.status_code == 202
    assert response.json()["rejected_count"] == 1
    assert response.json()["errors"][0]["field"] == "device_code"


def test_future_timestamp_is_rejected(client: TestClient) -> None:
    future = datetime.now(UTC) + timedelta(minutes=6)
    response = client.post(
        "/api/v1/ingest/measurements",
        json={
            "source": "gateway",
            "records": [record(measured_at=future.isoformat().replace("+00:00", "Z"))],
        },
        headers=headers(),
    )
    assert response.status_code == 202
    assert response.json()["rejected_count"] == 1
    assert response.json()["errors"][0]["field"] == "measured_at"


def test_unauthorised_batch_is_rejected_whole(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ingest/measurements",
        json={"source": "gateway", "records": [record(index=4)]},
        headers={"X-Ingest-Key": "wrong-key"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_INGEST_KEY"


def test_ingestion_is_rate_limited_per_client(client: TestClient) -> None:
    payload = {"source": "gateway", "records": [record(index=7)]}
    for _ in range(120):
        response = client.post(
            "/api/v1/ingest/measurements", json=payload, headers=headers()
        )
        assert response.status_code == 202

    limited = client.post(
        "/api/v1/ingest/measurements", json=payload, headers=headers()
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_counter_decrease_requires_reset_flag(client: TestClient) -> None:
    baseline = record(index=5, energy_kwh_total=900_000_000_000)
    decreased = record(index=6, energy_kwh_total=1)
    baseline_response = client.post(
        "/api/v1/ingest/measurements",
        json={"source": "gateway", "records": [baseline]},
        headers=headers(),
    )
    assert baseline_response.json()["accepted_count"] == 1
    rejected = client.post(
        "/api/v1/ingest/measurements",
        json={"source": "gateway", "records": [decreased]},
        headers=headers(),
    )
    assert rejected.json()["rejected_count"] == 1
    accepted = client.post(
        "/api/v1/ingest/measurements",
        json={
            "source": "gateway",
            "records": [dict(decreased, energy_reset=True)],
        },
        headers=headers(),
    )
    assert accepted.json()["accepted_count"] == 1


def test_sixty_record_batch_meets_local_two_second_target(
    client: TestClient,
) -> None:
    batch = [record(index=10 + item) for item in range(60)]
    started = perf_counter()
    response = client.post(
        "/api/v1/ingest/measurements",
        json={"source": "gateway", "records": batch},
        headers=headers(),
    )
    elapsed = perf_counter() - started
    assert response.status_code == 202
    assert response.json()["accepted_count"] == 60
    assert elapsed < 2.0, f"60-record batch took {elapsed:.3f} seconds"
