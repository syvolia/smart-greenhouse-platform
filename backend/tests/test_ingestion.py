from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.sensor_reading import SensorReading


@pytest.fixture
def sensor_ids(client: TestClient, seeded_db: None) -> list[int]:
    ids: list[int] = []
    for gh in client.get("/greenhouses").json():
        for zone in client.get(f"/greenhouses/{gh['id']}/zones").json():
            for s in client.get(f"/zones/{zone['id']}/sensors").json():
                ids.append(s["id"])
    return ids


def _reading(sensor_id: int, ts: datetime, value: float = 22.5) -> dict:
    return {"sensor_id": sensor_id, "timestamp": ts.isoformat(), "value": value}


def test_valid_batch_ingestion(
    client: TestClient, sensor_ids: list[int]
) -> None:
    ts = datetime.now(timezone.utc)
    payload = {"readings": [_reading(sid, ts) for sid in sensor_ids[:10]]}
    r = client.post("/ingestion/sensor-readings", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body == {"received": 10, "inserted": 10, "rejected": 0, "duplicates": 0}


def test_invalid_sensor_ids_rejected(
    client: TestClient, sensor_ids: list[int]
) -> None:
    ts = datetime.now(timezone.utc)
    payload = {
        "readings": [
            _reading(sensor_ids[0], ts),
            _reading(999_999, ts),
            _reading(1_000_000, ts),
        ]
    }
    r = client.post("/ingestion/sensor-readings", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["received"] == 3
    assert body["inserted"] == 1
    assert body["rejected"] == 2
    assert body["duplicates"] == 0


def test_malformed_reading_returns_422(
    client: TestClient, sensor_ids: list[int]
) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    bad_payloads = [
        {"readings": [{"sensor_id": sensor_ids[0], "timestamp": ts}]},  # missing value
        {"readings": [{"sensor_id": sensor_ids[0], "value": 1.0}]},     # missing ts
        {"readings": [{"timestamp": ts, "value": 1.0}]},                # missing id
        {"readings": [{"sensor_id": -1, "timestamp": ts, "value": 1.0}]},  # id <= 0
        {"readings": "not-a-list"},
        {"wrong_key": []},
    ]
    for payload in bad_payloads:
        r = client.post("/ingestion/sensor-readings", json=payload)
        assert r.status_code == 422, payload


def test_duplicate_readings_are_idempotent(
    client: TestClient, sensor_ids: list[int]
) -> None:
    ts = datetime.now(timezone.utc)
    payload = {"readings": [_reading(sid, ts) for sid in sensor_ids[:5]]}

    first = client.post("/ingestion/sensor-readings", json=payload).json()
    assert first["inserted"] == 5
    assert first["duplicates"] == 0

    second = client.post("/ingestion/sensor-readings", json=payload).json()
    assert second["inserted"] == 0
    assert second["duplicates"] == 5


def test_empty_batch_returns_zeros(client: TestClient, seeded_db: None) -> None:
    r = client.post("/ingestion/sensor-readings", json={"readings": []})
    assert r.status_code == 201
    assert r.json() == {
        "received": 0, "inserted": 0, "rejected": 0, "duplicates": 0
    }


def test_database_persistence(
    client: TestClient, sensor_ids: list[int]
) -> None:
    ts = datetime.now(timezone.utc)
    payload = {"readings": [_reading(sensor_ids[0], ts, value=123.456)]}
    assert client.post("/ingestion/sensor-readings", json=payload).status_code == 201

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count(SensorReading.id)).where(
                SensorReading.sensor_id == sensor_ids[0],
                SensorReading.timestamp == ts,
            )
        )
        assert count == 1
        row = db.scalar(
            select(SensorReading).where(
                SensorReading.sensor_id == sensor_ids[0],
                SensorReading.timestamp == ts,
            )
        )
        assert row is not None
        assert float(row.value) == pytest.approx(123.456, abs=1e-3)