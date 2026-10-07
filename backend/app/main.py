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
from app.api.ml import router as ml_router
from app.api.recommendations import router as recommendations_router
from app.api.topology import router as topology_router
from app.api.zones import router as zones_router
from app.config import settings
from app.logging_config import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
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
        version="0.11.0",
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

    # Public
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(ingestion_router)

    # Protected (each router enforces its own RBAC)
    app.include_router(greenhouses_router)
    app.include_router(zones_router)
    app.include_router(topology_router)
    app.include_router(analytics_router)
    app.include_router(alerts_router)
    app.include_router(recommendations_router)
    app.include_router(ml_router)

    return app


app = create_app()