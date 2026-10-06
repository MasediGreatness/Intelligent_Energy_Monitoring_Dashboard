"""Validation and defaults for the fixed operational-settings contract."""

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.errors import ApplicationError

SETTING_DEFAULTS: dict[str, object] = {
    "demand_limit_kw": 50.0,
    "demand_interval_minutes": 15,
    "tariff_zar_per_kwh": 3.0,
    "timezone": "Africa/Johannesburg",
    "online_timeout_seconds": 10,
    "stale_timeout_seconds": 60,
    "simulator_profile": "normal",
}

SIMULATOR_PROFILES = {
    "normal",
    "peak_demand",
    "low_power_factor",
    "sudden_overconsumption",
    "device_dropout",
    "meter_reset",
}
DEMAND_INTERVALS = {1, 5, 15, 30, 60}


def _invalid(key: str, message: str) -> ApplicationError:
    return ApplicationError(
        status_code=422,
        code="INVALID_SETTING_VALUE",
        message=message,
        details={"field": "value", "key": key},
    )


def validate_setting_value(
    key: str, value: Any, current_values: dict[str, object]
) -> object:
    """Validate and normalize one setting against the complete current set."""
    if key not in SETTING_DEFAULTS:
        raise _invalid(key, "This setting is not part of the supported contract.")

    if key in {"demand_limit_kw", "tariff_zar_per_kwh"}:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _invalid(key, "The setting must be a number.")
        number = float(value)
        lower, upper = (0.0, 2000.0) if key == "demand_limit_kw" else (0.0, 100.0)
        if (
            key == "demand_limit_kw" and number <= lower
        ) or not lower <= number <= upper:
            raise _invalid(key, f"The setting must be within {lower:g} and {upper:g}.")
        return number

    if key == "demand_interval_minutes":
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value not in DEMAND_INTERVALS
        ):
            raise _invalid(key, "Demand interval must be 1, 5, 15, 30, or 60 minutes.")
        return value

    if key in {"online_timeout_seconds", "stale_timeout_seconds"}:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= 86400
        ):
            raise _invalid(
                key, "Timeout must be a whole number from 1 to 86400 seconds."
            )
        online = (
            value
            if key == "online_timeout_seconds"
            else current_values.get("online_timeout_seconds", 10)
        )
        stale = (
            value
            if key == "stale_timeout_seconds"
            else current_values.get("stale_timeout_seconds", 60)
        )
        if not isinstance(online, int) or not isinstance(stale, int) or stale <= online:
            raise _invalid(key, "Stale timeout must be greater than online timeout.")
        return value

    if key == "timezone":
        if not isinstance(value, str) or not value or len(value) > 100:
            raise _invalid(key, "Timezone must be a valid IANA timezone name.")
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise _invalid(key, "Timezone must be a valid IANA timezone name.") from exc
        return value

    if not isinstance(value, str) or value not in SIMULATOR_PROFILES:
        raise _invalid(key, "Simulator profile is not supported.")
    return value
