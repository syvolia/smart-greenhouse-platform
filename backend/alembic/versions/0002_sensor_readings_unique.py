"""add unique constraint on sensor_readings(sensor_id, timestamp)

Revision ID: 0002_unique_readings
Revises: 0001_initial
Create Date: 2026-01-02 00:00:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_unique_readings"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_sensor_readings_sensor_ts", table_name="sensor_readings")
    op.create_unique_constraint(
        "uq_sensor_readings_sensor_ts",
        "sensor_readings",
        ["sensor_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_sensor_readings_sensor_ts", "sensor_readings", type_="unique"
    )
    op.create_index(
        "ix_sensor_readings_sensor_ts",
        "sensor_readings",
        ["sensor_id", "timestamp"],
    )