data "azuread_client_config" "current" {
}

resource "azuread_application_registration" "github_actions" {
  display_name     = "github-actions-${var.robot_name}-${var.environment}"
  sign_in_audience = "AzureADMyOrg"
}

resource "azuread_service_principal" "github_actions" {
  client_id                    = azuread_application_registration.github_actions.client_id
  app_role_assignment_required = true
  owners                       = [data.azuread_client_config.current.object_id]
}

# This credential means that when GitHub requests a token with a
# given environment will have the appropriate permissions
resource "azuread_application_federated_identity_credential" "github" {
  display_name = "gha-${var.robot_name}-deploy-${var.environment}"

  application_id = azuread_application_registration.github_actions.id
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_repo}:environment:${var.environment}"
}

# We want our Github actions to be able to push to the container registry
resource "azurerm_role_assignment" "gha-container-push" {
  role_definition_name = "AcrPush"
  scope                = data.azurerm_container_registry.destiny_shared_infra.id
  principal_id         = azuread_service_principal.github_actions.object_id
}

# We want our GitHub Actions to be able to update the container apps
resource "azurerm_role_assignment" "gha-container-app-env-contributor" {
  role_definition_name = "Contributor"
  scope                = module.container_app_toy_robot.container_app_env_id
  principal_id         = azuread_service_principal.github_actions.object_id
}

resource "azurerm_role_assignment" "gha-container-app-contributor" {
  role_definition_name = "Contributor"
  scope                = module.container_app_toy_robot.container_app_id
  principal_id         = azuread_service_principal.github_actions.object_id
}
