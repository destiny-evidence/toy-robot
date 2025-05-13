# This demonstrates the infrastructure required to allow your robot to authenticate to against destiny repository

# Data Source - this already exists and is managed by destiny repository
# Get the destiny repository application
data "azuread_application" "destiny_repository" {
  display_name = var.destiny_repository_application_display_name
}

# Data Source - this already exists and is managed by destiny repository
# Get the service principal for the destiny repository application
data "azuread_service_principal" "destiny_repository" {
  client_id = data.azuread_application.destiny_repository.client_id
}

# This might already exist for you if your robot has already been deployed
# In this case, you can use a data resource instead https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/resource_group
resource "azurerm_resource_group" "robot_resource_group" {
  name     = "rg-${var.robot_name}-staging"
  location = "swedencentral"
}

# Create a user assigned identity for our client app
resource "azurerm_user_assigned_identity" "toy_robot" {
  location            = azurerm_resource_group.robot_resource_group.location # Replace the example!
  name                = var.robot_name
  resource_group_name = azurerm_resource_group.robot_resource_group.name # Replace the example!
}

# Finally create the role assignment for the client app
resource "azuread_app_role_assignment" "toy_robot" {
  app_role_id         = data.azuread_service_principal.destiny_repository.app_role_ids["robot"]
  principal_object_id = azurerm_user_assigned_identity.toy_robot.principal_id
  resource_object_id  = data.azuread_service_principal.destiny_repository.object_id
}

# This deploys the toy robot as a container application into Azure. You may choose to do this differently.
data "azurerm_container_registry" "destiny_shared_infra" {
  name                = var.container_registry_name
  resource_group_name = var.container_registry_resource_group_name
}

module "container_app_toy_robot" {
  source                          = "app.terraform.io/destiny-evidence/container-app/azure"
  version                         = "1.3.0"
  app_name                        = var.robot_name
  environment                     = "staging" # toy-robot is for an example enhancement flow only
  container_registry_id           = data.azurerm_container_registry.destiny_shared_infra.id
  container_registry_login_server = data.azurerm_container_registry.destiny_shared_infra.login_server
  resource_group_name             = azurerm_resource_group.robot_resource_group.name
  region                          = azurerm_resource_group.robot_resource_group.location

  # We're the api url for the destiny repository here, which the toy robot will use to authenticate against
  env_vars = [
    {
      name  = "AZURE_APPLICATION_URL"
      value = "api://${data.azuread_application.destiny_repository.client_id}"
    },
  ]

  # You can see here that we're passing the user assigned identity that we created above to the client application.
  # This identity has the robot role assignment and will allow the robot to authenticate with destiny repository
  identity = {
    id           = azurerm_user_assigned_identity.toy_robot.id
    principal_id = azurerm_user_assigned_identity.toy_robot.principal_id
    client_id    = azurerm_user_assigned_identity.toy_robot.client_id
  }
}
