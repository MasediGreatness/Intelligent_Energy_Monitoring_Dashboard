from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import (
    AnomalyStatus,
    Criticality,
    DataQuality,
    LifecycleStatus,
    PhaseType,
    Severity,
    UserRole,
)


def persisted_enum(enum_type: type[Any], name: str) -> Enum:
    return Enum(
        enum_type,
        name=name,
        values_callable=lambda items: [item.value for item in items],
    )


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(persisted_enum(UserRole, "user_role"))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    location: Mapped[str] = mapped_column(String(255))
    phase_type: Mapped[PhaseType] = mapped_column(
        persisted_enum(PhaseType, "phase_type")
    )
    rated_power_kw: Mapped[float] = mapped_column(Double)
    criticality: Mapped[Criticality] = mapped_column(
        persisted_enum(Criticality, "criticality")
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint("rated_power_kw > 0", name="ck_devices_rated_power_positive"),
    )


class Measurement(Base):
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    voltage_v: Mapped[float | None] = mapped_column(Double)
    current_a: Mapped[float | None] = mapped_column(Double)
    active_power_kw: Mapped[float | None] = mapped_column(Double)
    reactive_power_kvar: Mapped[float | None] = mapped_column(Double)
    apparent_power_kva: Mapped[float | None] = mapped_column(Double)
    power_factor: Mapped[float | None] = mapped_column(Double)
    frequency_hz: Mapped[float | None] = mapped_column(Double)
    energy_kwh_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    data_quality: Mapped[DataQuality] = mapped_column(
        persisted_enum(DataQuality, "data_quality")
    )
    __table_args__ = (
        UniqueConstraint(
            "device_id", "measured_at", name="uq_measurements_device_measured_at"
        ),
        CheckConstraint(
            "voltage_v IS NULL OR voltage_v BETWEEN 0 AND 1000",
            name="ck_measurements_voltage",
        ),
        CheckConstraint(
            "current_a IS NULL OR current_a BETWEEN 0 AND 2000",
            name="ck_measurements_current",
        ),
        CheckConstraint(
            "active_power_kw IS NULL OR active_power_kw BETWEEN -2000 AND 2000",
            name="ck_measurements_active_power",
        ),
        CheckConstraint(
            "power_factor IS NULL OR power_factor BETWEEN 0 AND 1",
            name="ck_measurements_power_factor",
        ),
        CheckConstraint(
            "frequency_hz IS NULL OR frequency_hz BETWEEN 40 AND 70",
            name="ck_measurements_frequency",
        ),
        CheckConstraint(
            "energy_kwh_total IS NULL OR energy_kwh_total >= 0",
            name="ck_measurements_energy",
        ),
        Index(
            "ix_measurements_device_measured_at_desc", "device_id", measured_at.desc()
        ),
        Index("ix_measurements_measured_at_desc", measured_at.desc()),
    )


class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[UUID | None] = mapped_column(ForeignKey("devices.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    target_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    horizon_minutes: Mapped[int]
    predicted_power_kw: Mapped[float] = mapped_column(Double)
    lower_kw: Mapped[float | None] = mapped_column(Double)
    upper_kw: Mapped[float | None] = mapped_column(Double)
    model_version: Mapped[str] = mapped_column(String(128))
    __table_args__ = (
        CheckConstraint("horizon_minutes > 0", name="ck_forecasts_horizon_positive"),
        CheckConstraint(
            "lower_kw IS NULL OR upper_kw IS NULL OR lower_kw <= upper_kw",
            name="ck_forecasts_bounds",
        ),
        Index("ix_forecasts_target_generated_desc", "target_at", generated_at.desc()),
    )


class Anomaly(Base):
    __tablename__ = "anomalies"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    anomaly_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[Severity] = mapped_column(persisted_enum(Severity, "severity"))
    metric: Mapped[str] = mapped_column(String(100))
    actual_value: Mapped[float | None] = mapped_column(Double)
    expected_value: Mapped[float | None] = mapped_column(Double)
    score: Mapped[float] = mapped_column(Double)
    explanation: Mapped[str] = mapped_column(Text)
    status: Mapped[AnomalyStatus] = mapped_column(
        persisted_enum(AnomalyStatus, "anomaly_status")
    )
    __table_args__ = (
        Index("ix_anomalies_status_detected_desc", "status", detected_at.desc()),
    )


class Alarm(Base):
    __tablename__ = "alarms"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_id: Mapped[UUID | None] = mapped_column(ForeignKey("devices.id"))
    source: Mapped[str] = mapped_column(String(100))
    alarm_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[Severity] = mapped_column(persisted_enum(Severity, "severity"))
    message: Mapped[str] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    acknowledgement_note: Mapped[str | None] = mapped_column(Text)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[LifecycleStatus] = mapped_column(
        persisted_enum(LifecycleStatus, "alarm_status")
    )
    __table_args__ = (
        Index(
            "ix_alarms_status_severity_triggered_desc",
            "status",
            "severity",
            triggered_at.desc(),
        ),
    )


class SystemEvent(Base):
    __tablename__ = "system_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(128))
    details_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default="{}"
    )
    __table_args__ = (Index("ix_system_events_event_at_desc", event_at.desc()),)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value_json: Mapped[Any] = mapped_column(JSON)
    description: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
