"""Contracts for role-protected dashboard mutations."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import Criticality, PhaseType
from app.schemas.read import AlarmItem, DeviceItem, SettingItem


class AlarmAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=1, max_length=2000)

    @field_validator("note", mode="before")
    @classmethod
    def strip_note(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AlarmAcknowledgeResponse(BaseModel):
    alarm: AlarmItem


class SettingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any


class SettingUpdateResponse(BaseModel):
    setting: SettingItem


class DeviceFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Z0-9][A-Z0-9_-]{0,63}$",
    )
    name: str = Field(min_length=1, max_length=160)
    location: str = Field(min_length=1, max_length=255)
    phase_type: PhaseType
    rated_power_kw: float = Field(gt=0, le=2000)
    criticality: Criticality
    enabled: bool = True

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("name", "location", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class DeviceCreateRequest(DeviceFields):
    pass


class DeviceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Z0-9][A-Z0-9_-]{0,63}$",
    )
    name: str | None = Field(default=None, min_length=1, max_length=160)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    phase_type: PhaseType | None = None
    rated_power_kw: float | None = Field(default=None, gt=0, le=2000)
    criticality: Criticality | None = None
    enabled: bool | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("name", "location", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_change(self) -> "DeviceUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one device field is required.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Device update fields cannot be null.")
        return self


class DeviceMutationResponse(BaseModel):
    device: DeviceItem
