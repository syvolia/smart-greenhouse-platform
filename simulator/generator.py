"""Realistic greenhouse sensor value generation.

Pure functions (plus a small per-sensor state dict) so they can be unit-tested
without any network or database access.
"""
import math
import random
from datetime import datetime
from typing import Dict, Tuple

TARGET_KEY_BY_SENSOR = {
    "temperature": "temperature",
    "humidity": "humidity",
    "soil_moisture": "soil_moisture",
}

# Days per second notion — used only for soil-moisture decay per cycle.
SOIL_MOISTURE_DECAY_PER_CYCLE = 0.15
IRRIGATION_EVENT_PROBABILITY = 0.02
IRRIGATION_BURST_LITERS_PER_MIN = (2.0, 6.0)
SOIL_MOISTURE_BURST_PERCENT = (8.0, 15.0)


def _daylight_factor(now: datetime) -> float:
    """1.0 at solar noon (~12:00 local), 0.0 overnight.

    Uses a simple sine across the 06:00–18:00 window.
    """
    hour = now.hour + now.minute / 60.0 + now.second / 3600.0
    if hour < 6.0 or hour > 18.0:
        return 0.0
    return max(0.0, math.sin(math.pi * (hour - 6.0) / 12.0))


def generate_reading(
    sensor_type: str,
    targets: Dict[str, Tuple[float, float]],
    now: datetime,
    sensor_state: Dict[str, float],
    rng: random.Random,
    anomaly_probability: float = 0.02,
) -> float:
    """Return one realistic reading for the given sensor type.

    targets: {"temperature": (min,max), "humidity": (min,max),
              "soil_moisture": (min,max)}
    sensor_state: mutable dict per sensor; persists soil-moisture value.
    """
    daylight = _daylight_factor(now)

    if sensor_type == "temperature":
        lo, hi = targets["temperature"]
        mid = (lo + hi) / 2.0
        amp = (hi - lo) / 2.0 * 0.9
        value = mid + amp * (2.0 * daylight - 1.0) + rng.gauss(0.0, 0.3)

    elif sensor_type == "humidity":
        lo, hi = targets["humidity"]
        mid = (lo + hi) / 2.0
        amp = (hi - lo) / 2.0 * 0.7
        # Inverse relationship with temperature -> humidity peaks at night
        value = mid - amp * (2.0 * daylight - 1.0) + rng.gauss(0.0, 1.5)
        value = max(0.0, min(100.0, value))

    elif sensor_type == "light":
        max_lux = 50_000.0
        value = max_lux * daylight + rng.gauss(0.0, 500.0)
        value = max(0.0, value)

    elif sensor_type == "soil_moisture":
        lo, hi = targets["soil_moisture"]
        current = sensor_state.get("soil_moisture", (lo + hi) / 2.0)
        current -= SOIL_MOISTURE_DECAY_PER_CYCLE
        if rng.random() < IRRIGATION_EVENT_PROBABILITY:
            current += rng.uniform(*SOIL_MOISTURE_BURST_PERCENT)
        current = max(lo * 0.8, min(hi * 1.1, current))
        sensor_state["soil_moisture"] = current
        value = current + rng.gauss(0.0, 0.5)

    elif sensor_type == "co2":
        # Photosynthesis pulls CO2 down during daylight
        value = 800.0 - 200.0 * daylight + rng.gauss(0.0, 30.0)
        value = max(350.0, value)

    elif sensor_type == "irrigation":
        if rng.random() < IRRIGATION_EVENT_PROBABILITY:
            value = rng.uniform(*IRRIGATION_BURST_LITERS_PER_MIN)
        else:
            value = 0.0

    else:
        raise ValueError(f"Unsupported sensor_type: {sensor_type!r}")

    if rng.random() < anomaly_probability:
        # Push the value well outside the normal band. Later phases will
        # flag these via anomaly detection.
        scale = rng.uniform(1.5, 2.5)
        value = value * scale if value > 0 else rng.uniform(-10.0, -1.0)

    return round(float(value), 4)