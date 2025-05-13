"""API config parsing and model."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings model for API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_application_url: str
    azure_client_id: str
    env: str = "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get a cached settings object."""
    return Settings()  # type: ignore[call-arg]
