from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ultra OpenCart PRO"
    app_env: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./ultra_opencart.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    # Sync Scheduler
    sync_interval_seconds: int = 60
    sync_page_size: int = 100
    sync_max_retries: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
