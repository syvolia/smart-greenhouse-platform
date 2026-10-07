from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.topology import GreenhouseTopology
from app.services import topology_service

router = APIRouter(tags=["topology"])


@router.get("/topology", response_model=list[GreenhouseTopology])
def get_topology(db: Session = Depends(get_db)) -> list[GreenhouseTopology]:
    return topology_service.get_topology(db)
