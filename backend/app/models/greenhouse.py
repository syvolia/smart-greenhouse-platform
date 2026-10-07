from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import GreenhouseStatus

if TYPE_CHECKING:
    from app.models.zone import Zone


class Greenhouse(Base):
    __tablename__ = "greenhouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[GreenhouseStatus] = mapped_column(
        SAEnum(
            GreenhouseStatus,
            name="greenhouse_status",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=GreenhouseStatus.ACTIVE,
        server_default=GreenhouseStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    zones: Mapped[List["Zone"]] = relationship(
        back_populates="greenhouse",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Zone.id",
    )