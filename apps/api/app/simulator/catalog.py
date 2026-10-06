"""Stable simulated device catalog."""

from dataclasses import dataclass
from uuid import UUID, uuid5

SIMULATOR_NAMESPACE = UUID("7d726d5a-683f-5aba-961a-f8db4128be21")


@dataclass(frozen=True)
class DeviceDefinition:
    id: UUID
    code: str
    name: str
    location: str
    phase_type: str
    rated_power_kw: float
    criticality: str
    base_energy_kwh: float
    profile: str


def _device(
    code: str,
    name: str,
    location: str,
    phase_type: str,
    rated_power_kw: float,
    criticality: str,
    base_energy_kwh: float,
    profile: str,
) -> DeviceDefinition:
    return DeviceDefinition(
        id=uuid5(SIMULATOR_NAMESPACE, code),
        code=code,
        name=name,
        location=location,
        phase_type=phase_type,
        rated_power_kw=rated_power_kw,
        criticality=criticality,
        base_energy_kwh=base_energy_kwh,
        profile=profile,
    )


DEVICES = (
    _device(
        "LOAD-001",
        "Main Air Compressor",
        "Utilities Bay",
        "three_phase",
        18.5,
        "critical",
        1842.376,
        "compressor",
    ),
    _device(
        "LOAD-002",
        "Line Conveyor Motor",
        "Production Line 7",
        "three_phase",
        11.0,
        "high",
        962.140,
        "conveyor",
    ),
    _device(
        "LOAD-003",
        "Process Water Pump",
        "Pump Room",
        "three_phase",
        7.5,
        "high",
        731.205,
        "pump",
    ),
    _device(
        "LOAD-004",
        "Process Heater",
        "Production Line 7",
        "three_phase",
        15.0,
        "medium",
        1264.880,
        "heater",
    ),
    _device(
        "LOAD-005",
        "Factory Lighting",
        "Main Factory Floor",
        "single_phase",
        5.0,
        "low",
        418.550,
        "lighting",
    ),
)
