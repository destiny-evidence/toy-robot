"""API config parsing and model."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings model for API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_application_url: str | None = Field(
        default=None, description="application url for destiny repository."
    )
    azure_client_id: str | None = Field(
        default=None,
        description="client id for the toy robot application registration.",
    )
    env: str = "production"
    access_token: str | None = Field(
        default=None,
        description="Only needed if in dev environment and authing against Azure.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get a cached settings object."""
    return Settings()  # type: ignore[call-arg]
