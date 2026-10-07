from enum import Enum


class GreenhouseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SOIL_MOISTURE = "soil_moisture"
    LIGHT = "light"
    CO2 = "co2"
    IRRIGATION = "irrigation"


class SensorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class AlertType(str, Enum):
    THRESHOLD_HIGH = "threshold_high"
    THRESHOLD_LOW = "threshold_low"
    ANOMALY = "anomaly"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class RecommendationType(str, Enum):
    IRRIGATION_NEEDED = "irrigation_needed"
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    HUMIDITY_HIGH_RISK = "humidity_high_risk"
    CO2_OUT_OF_RANGE = "co2_out_of_range"
    ANOMALY_REVIEW = "anomaly_review"
    YIELD_RISK = "yield_risk"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationStatus(str, Enum):
    OPEN = "open"
    DISMISSED = "dismissed"
    COMPLETED = "completed"

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGRONOMIST = "agronomist"
    VIEWER = "viewer"