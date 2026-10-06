from __future__ import annotations

from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated process configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=True
    )

    APP_ENV: Literal["development", "demo", "gateway", "test"] = "development"
    DATABASE_URL: str
    APP_SECRET_KEY: SecretStr = Field(min_length=32)
    INGEST_API_KEY: SecretStr = Field(min_length=24)
    DEFAULT_TIMEZONE: str = "Africa/Johannesburg"
    ONLINE_TIMEOUT_SECONDS: int = Field(default=10, ge=1)
    STALE_TIMEOUT_SECONDS: int = Field(default=60, ge=2)
    DEMAND_INTERVAL_MINUTES: int = Field(default=15, ge=1, le=60)
    DEMAND_LIMIT_KW: float = Field(default=50.0, gt=0)
    TARIFF_ZAR_PER_KWH: float = Field(default=3.0, ge=0)
    SIMULATOR_ENABLED: bool = True
    SIMULATOR_SEED: int = 118
    AUTH_SESSION_MINUTES: int = Field(default=30, ge=1, le=1440)
    SESSION_COOKIE_SECURE: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def require_postgresql_psycopg(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("DEFAULT_TIMEZONE")
    @classmethod
    def require_valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("DEFAULT_TIMEZONE must be an IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def require_ordered_timeouts(self) -> Settings:
        if self.STALE_TIMEOUT_SECONDS <= self.ONLINE_TIMEOUT_SECONDS:
            raise ValueError("STALE_TIMEOUT_SECONDS must exceed ONLINE_TIMEOUT_SECONDS")
        return self


@lru_cache
def get_settings() -> Settings:
    # Values are required from the environment by pydantic-settings at runtime.
    return Settings()
