import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ingestion import IngestionStats, SensorReadingBatch
from app.services import ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post(
    "/sensor-readings",
    response_model=IngestionStats,
    status_code=status.HTTP_201_CREATED,
)
def ingest_sensor_readings(
    batch: SensorReadingBatch,
    db: Session = Depends(get_db),
) -> IngestionStats:
    stats = ingestion_service.ingest_batch(db, batch.readings)
    return IngestionStats(**stats)