"""Authentication strategies for the Toy Robot."""

from enum import StrEnum

from destiny_sdk.auth import AuthMethod, AzureJwtAuth, CachingStrategyAuth, SuccessAuth

from app.config import get_settings

settings = get_settings()


class AuthScopes(StrEnum):
    """Auth Scopes known to the Toy Robot."""

    TOY_COLLECTOR = "toy.collector"


def auth_strategy() -> AuthMethod:
    """Select the authentication strategy to use."""
    if settings.env == "dev":
        return SuccessAuth()

    return AzureJwtAuth(
        tenant_id="not yet", application_id="not yet", scope=AuthScopes.TOY_COLLECTOR
    )


toy_collector_auth = CachingStrategyAuth(selector=auth_strategy)
