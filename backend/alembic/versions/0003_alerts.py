"""add alerts table and enums

Revision ID: 0003_alerts
Revises: 0002_unique_readings
Create Date: 2026-01-03 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_alerts"
down_revision: Union[str, None] = "0002_unique_readings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    alert_type = postgresql.ENUM(
        "threshold_high", "threshold_low", "anomaly",
        name="alert_type", create_type=False,
    )
    alert_severity = postgresql.ENUM(
        "info", "warning", "critical",
        name="alert_severity", create_type=False,
    )
    alert_status = postgresql.ENUM(
        "open", "acknowledged", "resolved",
        name="alert_status", create_type=False,
    )
    alert_type.create(bind, checkfirst=True)
    alert_severity.create(bind, checkfirst=True)
    alert_status.create(bind, checkfirst=True)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "greenhouse_id", sa.Integer,
            sa.ForeignKey("greenhouses.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "zone_id", sa.Integer,
            sa.ForeignKey("zones.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column(
            "sensor_id", sa.Integer,
            sa.ForeignKey("sensors.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("alert_type", alert_type, nullable=False),
        sa.Column("severity", alert_severity, nullable=False),
        sa.Column("status", alert_status, nullable=False, server_default="open"),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=True),
        sa.Column("threshold", sa.String(120), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerts_greenhouse_id", "alerts", ["greenhouse_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index(
        "uq_alerts_open_per_sensor_type",
        "alerts",
        ["sensor_id", "alert_type"],
        unique=True,
        postgresql_where=sa.text("status IN ('open', 'acknowledged')"),
    )


def downgrade() -> None:
    op.drop_index("uq_alerts_open_per_sensor_type", table_name="alerts")
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_greenhouse_id", table_name="alerts")
    op.drop_table("alerts")

    bind = op.get_bind()
    postgresql.ENUM(name="alert_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="alert_severity").drop(bind, checkfirst=True)
    postgresql.ENUM(name="alert_type").drop(bind, checkfirst=True)