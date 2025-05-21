"""API config parsing and model."""

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings model for API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    access_token: str | None = Field(
        default=None,
        description="Token needed if in dev environment and authing against Azure.",
    )
    azure_client_id: str | None = Field(
        default=None,
        description="client id for the toy robot application registration.",
    )
    azure_application_id: str = Field(
        description="Id of the application registration for toy robot"
    )
    azure_tenant_id: str = Field(
        description="Id of the tenant that the toy robot is deployed in."
    )
    destiny_repository_application_url: str | None = Field(
        default=None,
        description="application url for destiny repository, starts with api://.",
    )
    destiny_repository_url: HttpUrl

    env: str = "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get a cached settings object."""
    return Settings()  # type: ignore[call-arg]
