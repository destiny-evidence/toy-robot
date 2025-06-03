"""API config parsing and model."""

from enum import StrEnum
from functools import lru_cache

from pydantic import UUID4, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """
    Environment that the toy robot is running in.

    As this robot is for demo purposes only, we do not accept `production` as a value

    **Allowed values**:
    - `local`: The robot is running locally
    - `development`: The robot is running in development
    - `staging`: The robot is running in staging
    - `test`: The robot is running as a test fixture for the repository
    """

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    TEST = "test"


class Settings(BaseSettings):
    """Settings model for API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    robot_secret: str | None = Field(
        default=None,
        description="Secret needed for communicating with destiny repo.",
    )
    robot_id: UUID4 | None = Field(
        default=None,
        description="Client id needed for communicating with destiny repository.",
    )
    destiny_repository_url: HttpUrl

    env: Environment = Environment.STAGING


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get a cached settings object."""
    return Settings()  # type: ignore[call-arg]
