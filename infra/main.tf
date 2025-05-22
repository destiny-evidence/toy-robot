# This demonstrates the infrastructure required to allow your robot to authenticate to against destiny repository.

# Required Data Source - this already exists and is managed by destiny repository.
# Get the destiny repository application.
data "azuread_application" "destiny_repository" {
  display_name = var.destiny_repository_application_display_name
}

# Required Data Source - this already exists and is managed by destiny repository.
# Get the service principal for the destiny repository application.
data "azuread_service_principal" "destiny_repository" {
  client_id = data.azuread_application.destiny_repository.client_id
}

# This might exist for you if your robot has already been deployed.
# In this case, you can use a data resource instead https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/resource_group
resource "azurerm_resource_group" "robot_resource_group" {
  name     = "rg-${var.robot_name}-${var.environment}"
  location = "swedencentral"
}

# Create a user assigned identity for our robot. This is the identity used when authenticating.
resource "azurerm_user_assigned_identity" "toy_robot" {
  location            = azurerm_resource_group.robot_resource_group.location
  name                = var.robot_name
  resource_group_name = azurerm_resource_group.robot_resource_group.name
}

# Finally create the role assignment for our robot
resource "azuread_app_role_assignment" "toy_robot_to_destiny_repository" {
  app_role_id         = data.azuread_service_principal.destiny_repository.app_role_ids["robot"]
  principal_object_id = azurerm_user_assigned_identity.toy_robot.principal_id
  resource_object_id  = data.azuread_service_principal.destiny_repository.object_id
}

# This demonstrates the infrastructure required for destiny repository to authenticate against your robot

# Required Data Source - this already exists and is managed by destiny repository.
# Get the managed identity for destiny repository
data "azurerm_user_assigned_identity" "destiny_repository" {
  name                = var.destiny_repository_managed_identity_name
  resource_group_name = var.destiny_repository_resource_group_name
}

# Required Data Source - this already exists
# Get the configuration of our azuread provider
data "azuread_client_config" "current" {
}

# Create an application registration for the robot
resource "azuread_application_registration" "toy_robot" {
  display_name                   = "${var.robot_name}-${var.environment}"
  sign_in_audience               = "AzureADMyOrg"
  requested_access_token_version = 1
}

# Create a service principal for our robot
resource "azuread_service_principal" "toy_robot" {
  client_id                    = azuread_application_registration.toy_robot.client_id
  app_role_assignment_required = true
  owners                       = [data.azuread_client_config.current.object_id]
}

# Create a random uuid to use as the role id
resource "random_uuid" "toy_collector_role" {}

# Create an app role for the robots authentication scope.
# In this case "toy.collector"
resource "azuread_application_app_role" "toy_collector" {
  application_id       = azuread_application_registration.toy_robot.id
  allowed_member_types = ["User", "Application"]
  description          = "Toy collectors can request toy enhancements"
  display_name         = "Toy Collector"
  role_id              = random_uuid.toy_collector_role.result
  value                = "toy.collector" # This needs to match the value defined in AuthScopes in app/auth.py
}

# Assign the app role to the destiny repository managed identity
resource "azuread_app_role_assignment" "destiny_repository_to_toy_robot" {
  app_role_id         = azuread_application_app_role.toy_collector.role_id
  principal_object_id = data.azurerm_user_assigned_identity.destiny_repository.principal_id
  resource_object_id  = azuread_service_principal.toy_robot.object_id
}

# This deploys the toy robot as a container application into Azure. You may choose to do this differently.

# This is where the container app will pull images from
data "azurerm_container_registry" "destiny_shared_infra" {
  name                = var.container_registry_name
  resource_group_name = var.container_registry_resource_group_name
}

# This creates a container app to run the toy robot in
module "container_app_toy_robot" {
  source                          = "app.terraform.io/destiny-evidence/container-app/azure"
  version                         = "1.3.0"
  app_name                        = var.robot_name
  environment                     = var.environment # toy-robot is for an example enhancement flow only.
  container_registry_id           = data.azurerm_container_registry.destiny_shared_infra.id
  container_registry_login_server = data.azurerm_container_registry.destiny_shared_infra.login_server
  resource_group_name             = azurerm_resource_group.robot_resource_group.name
  region                          = azurerm_resource_group.robot_resource_group.location

  # We're the api url for the destiny repository here, which the toy robot will use to authenticate against.
  # The necessaary `AZURE_CLIENT_ID` environment variable is set by the container app module.
  env_vars = [
    {
      name  = "AZURE_APPLICATION_ID"
      value = azuread_application_registration.toy_robot.client_id
    },
    {
      name  = "AZURE_TENANT_ID"
      value = data.azuread_client_config.current.tenant_id
    },
    {
      name  = "DESTINY_REPOSITORY_APPLICATION_URL"
      value = "api://${data.azuread_application.destiny_repository.client_id}"
    },
    {
      name  = "DESTINY_REPOSITORY_URL"
      value = var.destiny_repository_url
    },
  ]

  # Ingress changes will be ignored to avoid messing up manual custom domain config.
  # See https://github.com/hashicorp/terraform-provider-azurerm/issues/21866#issuecomment-1755381572.
  ingress = {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8001
    transport                  = "auto"
    traffic_weight = {
      latest_revision = true
      percentage      = 100
    }
  }

  # You can see here that we're passing the user assigned identity that we created above to the client application.
  # This identity has the robot role assignment and will allow the robot to authenticate with destiny repository.
  identity = {
    id           = azurerm_user_assigned_identity.toy_robot.id
    principal_id = azurerm_user_assigned_identity.toy_robot.principal_id
    client_id    = azurerm_user_assigned_identity.toy_robot.client_id
  }
}
