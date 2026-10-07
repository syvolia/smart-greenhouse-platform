import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import any_user, require_admin
from app.models.user import User
from app.schemas.ml import (
    ModelInfoResponse,
    YieldPredictionRequest,
    YieldPredictionResponse,
)
from app.services import ml_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/predict-yield", response_model=YieldPredictionResponse)
def predict_yield(
    req: YieldPredictionRequest,
    _user: User = Depends(any_user),
) -> YieldPredictionResponse:
    try:
        result = ml_service.predict_yield(req)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Yield prediction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        ) from exc
    return YieldPredictionResponse(**result)


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(_admin: User = Depends(require_admin)) -> ModelInfoResponse:
    info = ml_service.model_info()
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded.",
        )
    return ModelInfoResponse(
        model_version=str(info.get("model_version", "unknown")),
        model_name=info.get("model_name", "unknown"),
        source=info.get("source", "unknown"),
        stage=info.get("stage"),
        run_id=info.get("run_id"),
        trained_at=info.get("trained_at", "unknown"),
        validation_metrics=info.get("validation_metrics", {}),
        test_metrics=info.get("test_metrics", {}),
        features=info.get("features", []),
    )


@router.post("/reload", status_code=status.HTTP_204_NO_CONTENT)
def reload_model(_admin: User = Depends(require_admin)) -> None:
    ml_service.reload()