from pydantic_settings import BaseSettings, SettingsConfigDict


class SimulatorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    backend_url: str = "http://backend:8000"
    simulator_interval_seconds: float = 5.0
    simulator_anomaly_probability: float = 0.02
    simulator_log_level: str = "INFO"
    simulator_request_timeout: float = 10.0
    simulator_topology_retry_seconds: float = 3.0
    simulator_topology_max_retries: int = 30


settings = SimulatorSettings()