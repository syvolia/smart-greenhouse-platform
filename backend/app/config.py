from functools import lru_cache
from typing import List
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env."""
    analytics_overview_window_hours: int = 24
    analytics_warning_tolerance_percent: float = 15.0
    alert_evaluation_enabled: bool = True
    alert_co2_min_ppm: int = 400
    alert_co2_max_ppm: int = 1500
    anomaly_window_size: int = 60
    anomaly_zscore_threshold: float = 4.0
    mlflow_tracking_uri: Optional[str] = None
    mlflow_model_name: str = "greenhouse-yield-predictor"
    mlflow_model_stage: str = "Production"
        # --- Recommendations ---
    recommendation_evaluation_enabled: bool = True
    # Number of consecutive recent readings that must exceed a target for a
    # "sustained" recommendation (temperature high/low).
    recommendation_sustained_window: int = 5
    # Threshold below which ML-predicted yield is considered at-risk (fraction)
    recommendation_yield_risk_ratio: float = 0.85
    # Per-crop yield baselines (kg/m²) used as ML reference points
    yield_baseline_tomato: float = 4.8
    yield_baseline_cucumber: float = 3.6
    yield_baseline_lettuce: float = 2.7
    yield_baseline_pepper: float = 3.2
        # --- Authentication ---
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # Bootstrap admin: created on first startup if no users exist.
    bootstrap_admin_email: Optional[str] = None
    bootstrap_admin_password: Optional[str] = None
    bootstrap_admin_full_name: str = "Bootstrap Admin"
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

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
