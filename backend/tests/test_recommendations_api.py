from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models.enums import RecommendationStatus, RecommendationType
from app.models.recommendation import Recommendation
from app.models.sensor_reading import SensorReading


@pytest.fixture
def zone_and_sensors(client: TestClient, seeded_db: None):
    zones = client.get("/greenhouses/1/zones").json()
    zone_id = zones[0]["id"]
    sensors = {s["sensor_type"]: s["id"] for s in client.get(f"/zones/{zone_id}/sensors").json()}
    return zone_id, sensors


def _wipe_recommendations():
    with SessionLocal() as db:
        db.execute(delete(Recommendation))
        db.commit()


def _ingest(client: TestClient, sensor_id: int, value: float) -> None:
    ts = datetime.now(timezone.utc)
    r = client.post(
        "/ingestion/sensor-readings",
        json={"readings": [{"sensor_id": sensor_id, "timestamp": ts.isoformat(), "value": value}]},
    )
    assert r.status_code == 201


def test_irrigation_recommendation_created(client, zone_and_sensors):
    _wipe_recommendations()
    zone_id, sensors = zone_and_sensors
    _ingest(client, sensors["soil_moisture"], 30.0)  # below 55 min

    r = client.get("/recommendations", params={"status": "open"})
    assert r.status_code == 200
    body = r.json()
    matching = [
        a for a in body["recommendations"]
        if a["recommendation_type"] == "irrigation_needed" and a["zone_id"] == zone_id
    ]
    assert matching, body


def test_high_temperature_sustained_recommendation(client, zone_and_sensors):
    _wipe_recommendations()
    zone_id, sensors = zone_and_sensors
    # Feed 6 consecutive hot readings (window requires 5)
    for i in range(6):
        _ingest(client, sensors["temperature"], 30.0 + i * 0.1)
    r = client.get("/recommendations", params={"status": "open"})
    assert r.status_code == 200
    body = r.json()
    matching = [
        a for a in body["recommendations"]
        if a["recommendation_type"] == "temperature_high" and a["zone_id"] == zone_id
    ]
    assert matching, body


def test_dismiss_endpoint(client, zone_and_sensors):
    _wipe_recommendations()
    _, sensors = zone_and_sensors
    _ingest(client, sensors["soil_moisture"], 30.0)
    items = client.get("/recommendations", params={"status": "open"}).json()["recommendations"]
    assert items
    rid = items[0]["id"]
    r = client.post(f"/recommendations/{rid}/dismiss")
    assert r.status_code == 200
    assert r.json()["status"] == "dismissed"


def test_complete_endpoint(client, zone_and_sensors):
    _wipe_recommendations()
    _, sensors = zone_and_sensors
    _ingest(client, sensors["soil_moisture"], 30.0)
    items = client.get("/recommendations", params={"status": "open"}).json()["recommendations"]
    rid = items[0]["id"]
    r = client.post(f"/recommendations/{rid}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_auto_complete_on_recovery(client, zone_and_sensors):
    """When the underlying condition recovers, the open recommendation is closed."""
    _wipe_recommendations()
    zone_id, sensors = zone_and_sensors
    _ingest(client, sensors["soil_moisture"], 30.0)
    opens = client.get("/recommendations", params={"status": "open"}).json()["recommendations"]
    assert any(a["recommendation_type"] == "irrigation_needed" for a in opens)

    # Recover to normal
    _ingest(client, sensors["soil_moisture"], 70.0)
    opens_after = client.get("/recommendations", params={"status": "open"}).json()["recommendations"]
    assert not any(
        a["recommendation_type"] == "irrigation_needed"
        for a in opens_after
        if a["zone_id"] == zone_id
    )


def test_invalid_recommendation_id_returns_404(client, seeded_db):
    assert client.post("/recommendations/999999/dismiss").status_code == 404
    assert client.post("/recommendations/999999/complete").status_code == 404


def test_greenhouse_overview_includes_recommendation_counts(client, zone_and_sensors):
    _wipe_recommendations()
    _, sensors = zone_and_sensors
    _ingest(client, sensors["soil_moisture"], 30.0)
    body = client.get("/greenhouses/1/overview").json()
    assert "open_recommendations_count" in body
    assert body["open_recommendations_count"] >= 1