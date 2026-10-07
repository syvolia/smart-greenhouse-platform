import os
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Smart Greenhouse Intelligence Platform"
    app_env: str = "development"
    log_level: str = "INFO"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:5173"

    # Optional if DATABASE_URL is provided.
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # --- Analytics ---
    analytics_overview_window_hours: int = 24
    analytics_warning_tolerance_percent: float = 15.0

    # --- Alerts & anomaly detection ---
    alert_evaluation_enabled: bool = True
    alert_co2_min_ppm: int = 400
    alert_co2_max_ppm: int = 1500
    anomaly_window_size: int = 60
    anomaly_zscore_threshold: float = 4.0

    # --- Recommendations ---
    recommendation_evaluation_enabled: bool = True
    recommendation_sustained_window: int = 5
    recommendation_yield_risk_ratio: float = 0.85
    yield_baseline_tomato: float = 4.8
    yield_baseline_cucumber: float = 3.6
    yield_baseline_lettuce: float = 2.7
    yield_baseline_pepper: float = 3.2

    # --- Authentication ---
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    bootstrap_admin_email: Optional[str] = None
    bootstrap_admin_password: Optional[str] = None
    bootstrap_admin_full_name: str = "Bootstrap Admin"

    # --- MLflow ---
    mlflow_tracking_uri: Optional[str] = None
    mlflow_model_name: str = "greenhouse-yield-predictor"
    mlflow_model_stage: str = "Production"

    @field_validator("backend_cors_origins")
    @classmethod
    def _no_wildcard_with_credentials(cls, v: str) -> str:
        if "*" in v:
            raise ValueError(
                "Wildcard CORS origin is forbidden because credentials are enabled."
            )
        return v

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        """Return a SQLAlchemy URL.

        Precedence:
          1. DATABASE_URL env var (used for one-off migrations and hosted deployments)
          2. Assembled from POSTGRES_* (used by Docker Compose)
        """
        override = os.environ.get("DATABASE_URL")
        if override:
            # Normalize the scheme for SQLAlchemy + psycopg2.
            if override.startswith("postgres://"):
                override = override.replace(
                    "postgres://", "postgresql+psycopg2://", 1
                )
            elif override.startswith("postgresql://"):
                override = override.replace(
                    "postgresql://", "postgresql+psycopg2://", 1
                )
            return override

        if not all([self.postgres_user, self.postgres_password, self.postgres_db]):
            raise RuntimeError(
                "Database configuration missing. Either set DATABASE_URL, or "
                "set POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
            )
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()