from enum import StrEnum


class UserRole(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class PhaseType(StrEnum):
    SINGLE_PHASE = "single_phase"
    THREE_PHASE = "three_phase"


class Criticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataQuality(StrEnum):
    GOOD = "good"
    SUSPECT = "suspect"
    MISSING = "missing"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LifecycleStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    CLEARED = "cleared"


class AnomalyStatus(StrEnum):
    OPEN = "open"
    REVIEWED = "reviewed"
    CLEARED = "cleared"
