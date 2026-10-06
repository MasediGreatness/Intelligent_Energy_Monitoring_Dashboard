import pytest
from pydantic import ValidationError

from app.core.config import Settings


def values() -> dict[str, object]:
    return {
        "DATABASE_URL": "postgresql+psycopg://energy:@db:5432/energy",
        "APP_SECRET_KEY": "a" * 32,
        "INGEST_API_KEY": "b" * 24,
    }


def test_valid_configuration() -> None:
    settings = Settings(**values())  # type: ignore[arg-type]
    assert settings.DEFAULT_TIMEZONE == "Africa/Johannesburg"
    assert settings.SESSION_COOKIE_SECURE is False


def test_secure_session_cookie_configuration_is_explicit() -> None:
    config = values()
    config["SESSION_COOKIE_SECURE"] = True
    assert Settings(**config).SESSION_COOKIE_SECURE is True  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("DATABASE_URL", "sqlite:///x"),
        ("DEFAULT_TIMEZONE", "Not/AZone"),
        ("STALE_TIMEOUT_SECONDS", 10),
    ],
)
def test_invalid_configuration_is_rejected(field: str, value: object) -> None:
    config = values()
    config[field] = value
    with pytest.raises(ValidationError):
        Settings(**config)  # type: ignore[arg-type]
