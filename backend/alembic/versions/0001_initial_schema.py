"""initial schema: greenhouses, zones, sensors, sensor_readings

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    greenhouse_status = postgresql.ENUM(
        "active", "inactive", "maintenance",
        name="greenhouse_status", create_type=False,
    )
    sensor_type = postgresql.ENUM(
        "temperature", "humidity", "soil_moisture", "light", "co2", "irrigation",
        name="sensor_type", create_type=False,
    )
    sensor_status = postgresql.ENUM(
        "active", "inactive", "maintenance", "error",
        name="sensor_status", create_type=False,
    )

    greenhouse_status.create(bind, checkfirst=True)
    sensor_type.create(bind, checkfirst=True)
    sensor_status.create(bind, checkfirst=True)

    op.create_table(
        "greenhouses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("status", greenhouse_status, nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "zones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "greenhouse_id", sa.Integer,
            sa.ForeignKey("greenhouses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("crop_type", sa.String(80), nullable=False),
        sa.Column("target_temperature_min", sa.Numeric(6, 2), nullable=False),
        sa.Column("target_temperature_max", sa.Numeric(6, 2), nullable=False),
        sa.Column("target_humidity_min", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_humidity_max", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_soil_moisture_min", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_soil_moisture_max", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("greenhouse_id", "name", name="uq_zones_greenhouse_name"),
        sa.CheckConstraint(
            "target_temperature_min < target_temperature_max",
            name="ck_zones_temp_range",
        ),
        sa.CheckConstraint(
            "target_humidity_min < target_humidity_max",
            name="ck_zones_humidity_range",
        ),
        sa.CheckConstraint(
            "target_soil_moisture_min < target_soil_moisture_max",
            name="ck_zones_soil_moisture_range",
        ),
    )
    op.create_index("ix_zones_greenhouse_id", "zones", ["greenhouse_id"])

    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "zone_id", sa.Integer,
            sa.ForeignKey("zones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sensor_type", sensor_type, nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("status", sensor_status, nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("zone_id", "sensor_type", name="uq_sensors_zone_type"),
    )
    op.create_index("ix_sensors_zone_id", "sensors", ["zone_id"])

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "sensor_id", sa.Integer,
            sa.ForeignKey("sensors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
    )
    op.create_index(
        "ix_sensor_readings_sensor_ts",
        "sensor_readings",
        ["sensor_id", "timestamp"],
    )
    op.create_index(
        "ix_sensor_readings_timestamp",
        "sensor_readings",
        ["timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_readings_timestamp", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_sensor_ts", table_name="sensor_readings")
    op.drop_table("sensor_readings")

    op.drop_index("ix_sensors_zone_id", table_name="sensors")
    op.drop_table("sensors")

    op.drop_index("ix_zones_greenhouse_id", table_name="zones")
    op.drop_table("zones")

    op.drop_table("greenhouses")

    bind = op.get_bind()
    postgresql.ENUM(name="sensor_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="sensor_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="greenhouse_status").drop(bind, checkfirst=True)