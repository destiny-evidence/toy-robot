variable "destiny_repository_application_display_name" {
  description = "Display name of the destiny repository application we want the robot to be able to authenticate against."
}

variable "destiny_repository_resource_group_name" {
  description = "The name of the resource group the destiny repository application is deployed in."
}

variable "destiny_repository_managed_identity_name" {
  description = "The name of the user assigned identity that destiny repository will use to authenticate against the robot with."
}

variable "robot_name" {
  description = "Name of the robot."
}

# Variables below this line are for deploying the toy robot
# These may not be necessary for your use case
variable "container_registry_name" {
  description = "Name of the container registry where toy robot images are pushed."

}

variable "container_registry_resource_group_name" {
  description = "Name of the container registry resource group."
}

variable "destiny_repository_url" {
  description = "Url to configure the robot to post callbacks to."
}

variable "environment" {
  description = "Environment for the toy robot, should be either development or staging"
  default     = "staging"
}
