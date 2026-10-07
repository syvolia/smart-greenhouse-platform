"""add recommendations table and enums

Revision ID: 0005_recommendations
Revises: 0004_analytics_schemas
Create Date: 2026-01-05 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_recommendations"
down_revision: Union[str, None] = "0004_analytics_schemas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    rec_type = postgresql.ENUM(
        "irrigation_needed", "temperature_high", "temperature_low",
        "humidity_high_risk", "co2_out_of_range", "anomaly_review", "yield_risk",
        name="recommendation_type", create_type=False,
    )
    rec_priority = postgresql.ENUM(
        "low", "medium", "high", "critical",
        name="recommendation_priority", create_type=False,
    )
    rec_status = postgresql.ENUM(
        "open", "dismissed", "completed",
        name="recommendation_status", create_type=False,
    )
    rec_type.create(bind, checkfirst=True)
    rec_priority.create(bind, checkfirst=True)
    rec_status.create(bind, checkfirst=True)

    op.create_table(
        "recommendations",
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
            sa.ForeignKey("sensors.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("recommendation_type", rec_type, nullable=False),
        sa.Column("priority", rec_priority, nullable=False),
        sa.Column("status", rec_status, nullable=False, server_default="open"),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_recommendations_greenhouse_id", "recommendations", ["greenhouse_id"])
    op.create_index("ix_recommendations_zone_id", "recommendations", ["zone_id"])
    op.create_index("ix_recommendations_status", "recommendations", ["status"])
    op.create_index("ix_recommendations_priority", "recommendations", ["priority"])
    op.create_index("ix_recommendations_created_at", "recommendations", ["created_at"])

    # Partial unique index to prevent duplicate OPEN recommendations
    # per (greenhouse, zone (or 0), type). COALESCE handles zone_id IS NULL.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_recommendations_open_per_scope
        ON recommendations (greenhouse_id, (COALESCE(zone_id, 0)), recommendation_type)
        WHERE status = 'open'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_recommendations_open_per_scope")
    op.drop_index("ix_recommendations_created_at", table_name="recommendations")
    op.drop_index("ix_recommendations_priority", table_name="recommendations")
    op.drop_index("ix_recommendations_status", table_name="recommendations")
    op.drop_index("ix_recommendations_zone_id", table_name="recommendations")
    op.drop_index("ix_recommendations_greenhouse_id", table_name="recommendations")
    op.drop_table("recommendations")

    bind = op.get_bind()
    postgresql.ENUM(name="recommendation_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="recommendation_priority").drop(bind, checkfirst=True)
    postgresql.ENUM(name="recommendation_type").drop(bind, checkfirst=True)