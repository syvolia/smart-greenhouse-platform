import random
from datetime import datetime, timezone

import pytest

from simulator.generator import generate_reading

TARGETS = {
    "temperature": (18.0, 26.0),
    "humidity": (60.0, 80.0),
    "soil_moisture": (55.0, 75.0),
}


def _noon() -> datetime:
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _midnight() -> datetime:
    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "sensor_type",
    ["temperature", "humidity", "soil_moisture", "light", "co2", "irrigation"],
)
def test_generator_returns_float(sensor_type: str) -> None:
    rng = random.Random(42)
    value = generate_reading(
        sensor_type, TARGETS, _noon(), {}, rng, anomaly_probability=0.0
    )
    assert isinstance(value, float)


def test_light_is_higher_at_noon_than_midnight() -> None:
    rng = random.Random(1)
    noon = generate_reading("light", TARGETS, _noon(), {}, rng, 0.0)
    midnight = generate_reading("light", TARGETS, _midnight(), {}, rng, 0.0)
    assert noon > midnight
    assert midnight < 2000.0  # near zero overnight, allowing noise


def test_temperature_warmer_at_noon() -> None:
    rng = random.Random(2)
    noon = generate_reading("temperature", TARGETS, _noon(), {}, rng, 0.0)
    midnight = generate_reading("temperature", TARGETS, _midnight(), {}, rng, 0.0)
    assert noon > midnight


def test_humidity_inverse_of_temperature() -> None:
    rng = random.Random(3)
    noon = generate_reading("humidity", TARGETS, _noon(), {}, rng, 0.0)
    midnight = generate_reading("humidity", TARGETS, _midnight(), {}, rng, 0.0)
    assert midnight > noon


def test_soil_moisture_decreases_between_irrigations() -> None:
    rng = random.Random(4)
    state: dict = {}
    # Force no irrigation events by low probability loop
    values = [
        generate_reading("soil_moisture", TARGETS, _noon(), state, rng, 0.0)
        for _ in range(5)
    ]
    # With no irrigation, the value must monotonically trend down (allowing noise)
    assert values[-1] < values[0]


def test_anomaly_probability_one_produces_extreme_value() -> None:
    rng = random.Random(5)
    normal = generate_reading(
        "temperature", TARGETS, _noon(), {}, random.Random(5), anomaly_probability=0.0
    )
    anomalous = generate_reading(
        "temperature", TARGETS, _noon(), {}, rng, anomaly_probability=1.0
    )
    assert anomalous != normal