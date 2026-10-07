from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.models.sensor_reading import SensorReading

# Isolated 2020 window so simulator traffic (which writes "now") is excluded.
TEST_START = datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
TEST_END = datetime(2020, 6, 1, 23, 59, 59, tzinfo=timezone.utc)
TEST_TS = datetime(2020, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def zone_and_sensors(client: TestClient, seeded_db: None) -> tuple[int, dict[str, int]]:
    zones = client.get("/greenhouses/1/zones").json()
    zone_id = zones[0]["id"]
    sensors = client.get(f"/zones/{zone_id}/sensors").json()
    return zone_id, {s["sensor_type"]: s["id"] for s in sensors}


def _wipe_sensor_window(sensor_id: int) -> None:
    with SessionLocal() as db:
        db.execute(
            delete(SensorReading).where(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= TEST_START,
                SensorReading.timestamp <= TEST_END,
            )
        )
        db.commit()


def _insert(sensor_id: int, ts: datetime, value: float) -> None:
    with SessionLocal() as db:
        db.add(SensorReading(sensor_id=sensor_id, timestamp=ts, value=value))
        db.commit()


def _overview(client: TestClient, zone_id: int) -> dict:
    r = client.get(
        f"/zones/{zone_id}/overview",
        params={"start_time": TEST_START.isoformat(), "end_time": TEST_END.isoformat()},
    )
    assert r.status_code == 200
    return r.json()


def _reading(body: dict, sensor_type: str) -> dict:
    return next(x for x in body["readings"] if x["sensor_type"] == sensor_type)


# --- Zone overview statuses ------------------------------------------------


def test_zone_overview_normal(client, zone_and_sensors):
    zone_id, sensors = zone_and_sensors
    _wipe_sensor_window(sensors["temperature"])
    _insert(sensors["temperature"], TEST_TS, 22.0)  # inside 18–26
    body = _overview(client, zone_id)
    temp = _reading(body, "temperature")
    assert temp["status"] == "normal"
    assert temp["current_value"] == pytest.approx(22.0)
    assert temp["target_min"] == 18.0
    assert temp["target_max"] == 26.0


def test_zone_overview_warning(client, zone_and_sensors):
    zone_id, sensors = zone_and_sensors
    _wipe_sensor_window(sensors["temperature"])
    _insert(sensors["temperature"], TEST_TS, 26.5)  # 0.5 above max → within 15% band
    body = _overview(client, zone_id)
    assert _reading(body, "temperature")["status"] == "warning"


def test_zone_overview_critical(client, zone_and_sensors):
    zone_id, sensors = zone_and_sensors
    _wipe_sensor_window(sensors["temperature"])
    _insert(sensors["temperature"], TEST_TS, 32.0)  # way above max
    body = _overview(client, zone_id)
    assert _reading(body, "temperature")["status"] == "critical"
    assert body["overall_status"] == "critical"


def test_zone_overview_missing_data_is_unknown(client, zone_and_sensors):
    zone_id, sensors = zone_and_sensors
    _wipe_sensor_window(sensors["co2"])
    body = _overview(client, zone_id)
    co2 = _reading(body, "co2")
    assert co2["current_value"] is None
    assert co2["status"] == "unknown"
    assert co2["reading_count"] == 0


# --- Aggregations & latest -------------------------------------------------


def test_zone_overview_aggregations(client, zone_and_sensors):
    zone_id, sensors = zone_and_sensors
    _wipe_sensor_window(sensors["temperature"])
    _insert(sensors["temperature"], TEST_TS - timedelta(hours=2), 20.0)
    _insert(sensors["temperature"], TEST_TS - timedelta(hours=1), 22.0)
    _insert(sensors["temperature"], TEST_TS, 24.0)
    temp = _reading(_overview(client, zone_id), "temperature")
    assert temp["reading_count"] == 3
    assert temp["min_value"] == pytest.approx(20.0)
    assert temp["max_value"] == pytest.approx(24.0)
    assert temp["avg_value"] == pytest.approx(22.0, rel=1e-3)
    assert temp["current_value"] == pytest.approx(24.0)


# --- Greenhouse overview ---------------------------------------------------


def test_greenhouse_overview_structure(client, seeded_db):
    r = client.get("/greenhouses/1/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["greenhouse_id"] == 1
    assert len(body["zones"]) == 4
    for z in body["zones"]:
        assert len(z["readings"]) == 6  # 6 sensors per zone
    assert body["window_start"] < body["window_end"]


# --- Latest readings ------------------------------------------------------


def test_latest_readings_one_per_sensor(client, seeded_db):
    r = client.get("/greenhouses/1/latest-readings")
    assert r.status_code == 200
    body = r.json()
    assert body["greenhouse_id"] == 1
    # 4 zones × 6 sensors = 24
    assert len(body["readings"]) == 24
    sensor_ids = [x["sensor_id"] for x in body["readings"]]
    assert len(sensor_ids) == len(set(sensor_ids))


# --- History --------------------------------------------------------------


def test_sensor_history_time_filter(client, seeded_db):
    # Pick any sensor and inject deterministic readings
    sensors = client.get("/zones/1/sensors").json()
    sid = sensors[0]["id"]
    with SessionLocal() as db:
        db.execute(
            delete(SensorReading).where(
                SensorReading.sensor_id == sid,
                SensorReading.timestamp >= datetime(2030, 1, 1, tzinfo=timezone.utc),
            )
        )
        db.commit()
    future = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    _insert(sid, future, 1.0)
    _insert(sid, future + timedelta(minutes=1), 2.0)

    r = client.get(
        f"/sensors/{sid}/history",
        params={
            "start_time": (future - timedelta(minutes=1)).isoformat(),
            "end_time": (future + timedelta(minutes=2)).isoformat(),
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    values = sorted(x["value"] for x in body["readings"])
    assert values == [1.0, 2.0]


def test_greenhouse_history_sensor_type_filter(client, seeded_db):
    r = client.get(
        "/greenhouses/1/history",
        params={"sensor_type": "temperature", "limit": 10},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] <= 10
    # Verify each reading belongs to a temperature sensor
    temp_sensor_ids = {
        s["id"] for z in client.get("/greenhouses/1/zones").json()
        for s in client.get(f"/zones/{z['id']}/sensors").json()
        if s["sensor_type"] == "temperature"
    }
    assert all(x["sensor_id"] in temp_sensor_ids for x in body["readings"])


def test_history_pagination(client, seeded_db):
    sensors = client.get("/zones/1/sensors").json()
    sid = sensors[0]["id"]
    r1 = client.get(f"/sensors/{sid}/history", params={"limit": 5, "offset": 0})
    r2 = client.get(f"/sensors/{sid}/history", params={"limit": 5, "offset": 5})
    assert r1.status_code == r2.status_code == 200
    assert len(r1.json()["readings"]) <= 5
    assert len(r2.json()["readings"]) <= 5


# --- 404s ------------------------------------------------------------------


def test_invalid_ids_return_404(client, seeded_db):
    assert client.get("/greenhouses/999999/overview").status_code == 404
    assert client.get("/zones/999999/overview").status_code == 404
    assert client.get("/greenhouses/999999/latest-readings").status_code == 404
    assert client.get("/greenhouses/999999/history").status_code == 404
    assert client.get("/sensors/999999/history").status_code == 404


# --- Time zone handling ---------------------------------------------------


def test_naive_timestamps_treated_as_utc(client, zone_and_sensors):
    zone_id, _ = zone_and_sensors
    r = client.get(
        f"/zones/{zone_id}/overview",
        params={
            "start_time": "2020-06-01T00:00:00",
            "end_time": "2020-06-01T23:59:59",
        },
    )
    assert r.status_code == 200


def test_invalid_time_window_returns_422(client, zone_and_sensors):
    zone_id, _ = zone_and_sensors
    r = client.get(
        f"/zones/{zone_id}/overview",
        params={
            "start_time": "2020-06-02T00:00:00+00:00",
            "end_time": "2020-06-01T00:00:00+00:00",
        },
    )
    assert r.status_code == 422