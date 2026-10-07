from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.sensor import Sensor
from app.models.zone import Zone


def test_seeded_greenhouses_returned(
    client: TestClient, seeded_db: None
) -> None:
    r = client.get("/greenhouses")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 3
    assert len({g["name"] for g in body}) == 3


def test_each_greenhouse_has_four_zones(
    client: TestClient, seeded_db: None
) -> None:
    for gh in client.get("/greenhouses").json():
        r = client.get(f"/greenhouses/{gh['id']}/zones")
        assert r.status_code == 200
        assert len(r.json()) == 4


def test_each_zone_has_six_sensors(
    client: TestClient, seeded_db: None
) -> None:
    for gh in client.get("/greenhouses").json():
        for zone in client.get(f"/greenhouses/{gh['id']}/zones").json():
            r = client.get(f"/zones/{zone['id']}/sensors")
            assert r.status_code == 200
            assert len(r.json()) == 6


def test_sensor_ids_globally_unique(seeded_db: None) -> None:
    with SessionLocal() as db:
        total = db.scalar(select(func.count(Sensor.id)))
        distinct = db.scalar(select(func.count(func.distinct(Sensor.id))))
    assert total == 72
    assert total == distinct


def test_tomato_targets_exist(
    client: TestClient, seeded_db: None
) -> None:
    for gh in client.get("/greenhouses").json():
        for zone in client.get(f"/greenhouses/{gh['id']}/zones").json():
            assert zone["crop_type"] == "tomato"
            assert zone["target_temperature_min"] < zone["target_temperature_max"]
            assert zone["target_humidity_min"] < zone["target_humidity_max"]
            assert (
                zone["target_soil_moisture_min"] < zone["target_soil_moisture_max"]
            )
            assert 10 <= zone["target_temperature_min"] <= 30
            assert 15 <= zone["target_temperature_max"] <= 40
            assert 0 <= zone["target_humidity_min"] < zone["target_humidity_max"] <= 100
            assert (
                0
                <= zone["target_soil_moisture_min"]
                < zone["target_soil_moisture_max"]
                <= 100
            )


def test_invalid_greenhouse_id_returns_404(
    client: TestClient, seeded_db: None
) -> None:
    assert client.get("/greenhouses/999999").status_code == 404
    assert client.get("/greenhouses/999999/zones").status_code == 404


def test_invalid_zone_id_returns_404(
    client: TestClient, seeded_db: None
) -> None:
    assert client.get("/zones/999999/sensors").status_code == 404


def test_topology_returns_full_hierarchy(
    client: TestClient, seeded_db: None
) -> None:
    r = client.get("/topology")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 3
    for gh in body:
        assert len(gh["zones"]) == 4
        for zone in gh["zones"]:
            assert len(zone["sensors"]) == 6


def test_zone_service_uses_expected_columns(seeded_db: None) -> None:
    # Sanity check: crop_type is tomato across all zones
    with SessionLocal() as db:
        total = db.scalar(select(func.count(Zone.id)))
        tomatoes = db.scalar(
            select(func.count(Zone.id)).where(Zone.crop_type == "tomato")
        )
    assert total == 12
    assert total == tomatoes