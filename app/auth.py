"""Authentication strategies for the Toy Robot."""

from enum import StrEnum

import destiny_sdk

from app.config import Environment, get_settings

settings = get_settings()


class AuthScopes(StrEnum):
    """Auth Scopes known to the Toy Robot."""

    TOY_COLLECTOR = "toy.collector"


def auth_strategy_robot() -> destiny_sdk.auth.AuthMethod:
    """Select the authentication strategy to use on the robot's API endpoints."""
    # If we're running in the local environment, disable endpoint authentication.
    if settings.env in (Environment.LOCAL, Environment.TEST):
        return destiny_sdk.auth.SuccessAuth()

    return destiny_sdk.auth.AzureJwtAuth(
        tenant_id=settings.azure_tenant_id,
        application_id=settings.azure_application_id,
        scope=AuthScopes.TOY_COLLECTOR,
    )


toy_collector_auth = destiny_sdk.auth.CachingStrategyAuth(selector=auth_strategy_robot)


def destiny_repo_auth() -> destiny_sdk.client_auth.ClientAuthenticationMethod:
    """Select the authentication strategy to use comminicating with destiny repo."""
    # If we're running in the local environment, use an access token directly.
    if settings.env in (Environment.LOCAL, Environment.TEST):
        return destiny_sdk.client_auth.AccessTokenAuthentication(
            access_token=settings.access_token
        )

    return destiny_sdk.client_auth.ManagedIdentityAuthentication(
        azure_application_url=settings.destiny_repository_application_url,
        azure_client_id=settings.azure_client_id,
    )
