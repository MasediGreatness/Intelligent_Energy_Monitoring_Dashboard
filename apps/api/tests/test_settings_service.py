"""Exhaustive tests for the fixed operational-settings validation contract."""

import pytest

from app.core.errors import ApplicationError
from app.services.settings import SETTING_DEFAULTS, validate_setting_value


def validate(key: str, value: object) -> object:
    return validate_setting_value(key, value, SETTING_DEFAULTS.copy())


@pytest.mark.parametrize(
    ("key", "value", "expected"),
    [
        ("demand_limit_kw", 75, 75.0),
        ("tariff_zar_per_kwh", 3.25, 3.25),
        ("demand_interval_minutes", 30, 30),
        ("online_timeout_seconds", 20, 20),
        ("stale_timeout_seconds", 120, 120),
        ("timezone", "UTC", "UTC"),
        ("simulator_profile", "device_dropout", "device_dropout"),
    ],
)
def test_supported_setting_values_are_normalized(
    key: str, value: object, expected: object
) -> None:
    assert validate(key, value) == expected


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("unknown_setting", 1),
        ("demand_limit_kw", True),
        ("demand_limit_kw", 0),
        ("demand_limit_kw", 2001),
        ("tariff_zar_per_kwh", "3"),
        ("tariff_zar_per_kwh", -0.01),
        ("tariff_zar_per_kwh", 101),
        ("demand_interval_minutes", True),
        ("demand_interval_minutes", 10),
        ("online_timeout_seconds", 0),
        ("online_timeout_seconds", 86401),
        ("timezone", ""),
        ("timezone", "Not/AZone"),
        ("simulator_profile", 1),
        ("simulator_profile", "invented"),
    ],
)
def test_invalid_setting_values_use_the_standard_contract(
    key: str, value: object
) -> None:
    with pytest.raises(ApplicationError) as caught:
        validate(key, value)
    assert caught.value.status_code == 422
    assert caught.value.code == "INVALID_SETTING_VALUE"
    assert caught.value.details == {"field": "value", "key": key}


def test_timeout_relationship_rejects_invalid_current_types_and_order() -> None:
    with pytest.raises(ApplicationError):
        validate_setting_value(
            "online_timeout_seconds",
            60,
            SETTING_DEFAULTS | {"stale_timeout_seconds": 60},
        )
    with pytest.raises(ApplicationError):
        validate_setting_value(
            "stale_timeout_seconds",
            60,
            SETTING_DEFAULTS | {"online_timeout_seconds": "ten"},
        )
