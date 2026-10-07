"""create raw/staging/analytics schemas and raw views

Revision ID: 0004_analytics_schemas
Revises: 0003_alerts
Create Date: 2026-01-04 00:00:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_analytics_schemas"
down_revision: Union[str, None] = "0003_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS raw")
    op.execute("CREATE SCHEMA IF NOT EXISTS staging")
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    op.execute("""
        CREATE OR REPLACE VIEW raw.sensor_readings AS
        SELECT id, sensor_id, "timestamp", value
        FROM public.sensor_readings
    """)
    op.execute("""
        CREATE OR REPLACE VIEW raw.greenhouses AS
        SELECT id, name, location, status, created_at, updated_at
        FROM public.greenhouses
    """)
    op.execute("CREATE OR REPLACE VIEW raw.zones AS SELECT * FROM public.zones")
    op.execute("CREATE OR REPLACE VIEW raw.sensors AS SELECT * FROM public.sensors")
    op.execute("CREATE OR REPLACE VIEW raw.alerts AS SELECT * FROM public.alerts")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS raw.alerts")
    op.execute("DROP VIEW IF EXISTS raw.sensors")
    op.execute("DROP VIEW IF EXISTS raw.zones")
    op.execute("DROP VIEW IF EXISTS raw.greenhouses")
    op.execute("DROP VIEW IF EXISTS raw.sensor_readings")
    op.execute("DROP SCHEMA IF EXISTS analytics")
    op.execute("DROP SCHEMA IF EXISTS staging")
    op.execute("DROP SCHEMA IF EXISTS raw")