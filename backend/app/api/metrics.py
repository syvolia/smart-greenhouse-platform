from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sensor_reading import SensorReading

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=Response)
def metrics(db: Session = Depends(get_db)) -> Response:
    total = db.scalar(select(func.count(SensorReading.id))) or 0
    body = (
        "# HELP greenhouse_sensor_readings_total Total readings stored.\n"
        "# TYPE greenhouse_sensor_readings_total gauge\n"
        f"greenhouse_sensor_readings_total {total}\n"
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")