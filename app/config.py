"""Application configuration loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str
    database_sync_url: str

    # Application
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str

    # Scraper
    playwright_headless: bool = True
    scraper_timeout_seconds: int = 30
    scraper_delay_seconds: int = 2

    # Logging
    log_file_path: str = "logs/req-hunter.log"
    log_level: str = "INFO"
    log_max_bytes: int = 1_048_576
    log_backup_count: int = 3


settings = Settings()
