import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.greenhouses import router as greenhouses_router
from app.api.health import router as health_router
from app.api.ingestion import router as ingestion_router
from app.api.metrics import router as metrics_router
from app.api.ml import router as ml_router
from app.api.recommendations import router as recommendations_router
from app.api.topology import router as topology_router
from app.api.zones import router as zones_router
from app.config import settings
from app.logging_config import configure_logging
from app.middleware.error_handler import unhandled_exception_handler
from app.middleware.request_id import RequestIdMiddleware

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)

    # Refuse to boot with the placeholder secret in non-development environments.
    if settings.app_env != "development" and "change-me" in settings.secret_key.lower():
        raise RuntimeError(
            "SECRET_KEY still contains a placeholder value. Set a real secret."
        )

    # Bootstrap the initial admin user, if configured and if no users exist.
    try:
        from app.database import SessionLocal
        from app.services.auth_service import bootstrap_admin_if_needed

        with SessionLocal() as db:
            bootstrap_admin_if_needed(db)
    except Exception:  # noqa: BLE001
        logger.exception("Bootstrap admin step failed (continuing)")

    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.12.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Public
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(ingestion_router)
    app.include_router(metrics_router)

    # Protected
    app.include_router(greenhouses_router)
    app.include_router(zones_router)
    app.include_router(topology_router)
    app.include_router(analytics_router)
    app.include_router(alerts_router)
    app.include_router(recommendations_router)
    app.include_router(ml_router)

    return app


app = create_app()