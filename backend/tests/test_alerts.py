from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.enums import AlertStatus, AlertType
from app.models.sensor_reading import SensorReading


@pytest.fixture
def sensors_by_type(client: TestClient, seeded_db: None) -> dict[str, int]:
    """Return {sensor_type: sensor_id} for zone 1."""
    rows = client.get("/zones/1/sensors").json()
    return {r["sensor_type"]: r["id"] for r in rows}


def _wipe_alerts() -> None:
    with SessionLocal() as db:
        db.execute(delete(Alert))
        db.commit()


def _wipe_readings_for(sensor_id: int) -> None:
    with SessionLocal() as db:
        db.execute(delete(SensorReading).where(SensorReading.sensor_id == sensor_id))
        db.commit()


def _ingest(client: TestClient, sensor_id: int, value: float) -> None:
    ts = datetime.now(timezone.utc)
    r = client.post(
        "/ingestion/sensor-readings",
        json={"readings": [{"sensor_id": sensor_id, "timestamp": ts.isoformat(), "value": value}]},
    )
    assert r.status_code == 201


def test_high_temperature_creates_critical_alert(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)  # way above 26
    alerts = client.get("/alerts", params={"severity": "critical"}).json()["alerts"]
    matching = [a for a in alerts if a["sensor_id"] == sid]
    assert any(a["alert_type"] == "threshold_high" for a in matching)


def test_deduplicates_same_condition(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)
    _ingest(client, sid, 41.0)
    _ingest(client, sid, 42.0)
    with SessionLocal() as db:
        count = db.scalar(
            select(Alert.id).where(
                Alert.sensor_id == sid,
                Alert.alert_type == AlertType.THRESHOLD_HIGH,
                Alert.status == AlertStatus.OPEN,
            ).with_only_columns(Alert.id)
        )
        rows = db.scalars(
            select(Alert).where(
                Alert.sensor_id == sid,
                Alert.alert_type == AlertType.THRESHOLD_HIGH,
                Alert.status == AlertStatus.OPEN,
            )
        ).all()
    assert len(rows) == 1


def test_auto_resolves_when_value_returns_to_normal(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)
    _ingest(client, sid, 22.0)
    with SessionLocal() as db:
        open_alerts = db.scalars(
            select(Alert).where(
                Alert.sensor_id == sid,
                Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
            )
        ).all()
        resolved_alerts = db.scalars(
            select(Alert).where(
                Alert.sensor_id == sid,
                Alert.status == AlertStatus.RESOLVED,
            )
        ).all()
    assert len(open_alerts) == 0
    assert len(resolved_alerts) >= 1


def test_low_temperature_creates_threshold_low_alert(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 5.0)
    alerts = client.get("/alerts").json()["alerts"]
    matching = [
        a for a in alerts if a["sensor_id"] == sid and a["alert_type"] == "threshold_low"
    ]
    assert matching


def test_humidity_outside_range_alerts(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["humidity"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 95.0)
    alerts = client.get("/alerts", params={"greenhouse_id": 1}).json()["alerts"]
    assert any(a["sensor_id"] == sid for a in alerts)


def test_co2_outside_global_range_alerts(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["co2"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 3000.0)
    alerts = client.get("/alerts").json()["alerts"]
    matching = [a for a in alerts if a["sensor_id"] == sid]
    assert matching, alerts


def test_acknowledge_endpoint(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)
    alert_id = client.get("/alerts").json()["alerts"][0]["id"]
    r = client.post(f"/alerts/{alert_id}/acknowledge")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_at"] is not None


def test_resolve_endpoint(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)
    alert_id = client.get("/alerts").json()["alerts"][0]["id"]
    r = client.post(f"/alerts/{alert_id}/resolve")
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
    assert r.json()["resolved_at"] is not None


def test_alert_filters(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)
    r = client.get("/alerts", params={"severity": "critical", "status": "open"})
    assert r.status_code == 200
    body = r.json()
    assert all(a["severity"] == "critical" for a in body["alerts"])
    assert all(a["status"] == "open" for a in body["alerts"])


def test_invalid_alert_id_404(client, seeded_db):
    assert client.post("/alerts/999999/acknowledge").status_code == 404
    assert client.post("/alerts/999999/resolve").status_code == 404


def test_greenhouse_overview_includes_alert_counts(client, sensors_by_type):
    _wipe_alerts()
    sid = sensors_by_type["temperature"]
    _wipe_readings_for(sid)
    _ingest(client, sid, 40.0)
    body = client.get("/greenhouses/1/overview").json()
    assert "open_alerts_count" in body
    assert "critical_alerts_count" in body
    assert body["open_alerts_count"] >= 1


def test_anomaly_detector_flags_spike():
    from app.services.anomaly_service import ZScoreDetector

    detector = ZScoreDetector(window=30, threshold=3.0)
    # 30 stable values then a spike
    now = datetime.now(timezone.utc)
    readings = [(now - timedelta(seconds=i), 22.0) for i in range(30)]
    readings.insert(0, (now, 90.0))  # current point far from mean
    result = detector.detect(1, readings)
    assert result.is_anomaly
    assert result.z_score is not None and abs(result.z_score) > 3.0