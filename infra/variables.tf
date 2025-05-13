variable "destiny_repository_application_display_name" {
  description = "Display name of the destiny repository application we want the robot to be able to authenticate against."
}

# Variables below this line are for deploying the toy robot
# These may not be necessary for your use case
variable "robot_name" {
  description = "Name of the robot to deploy"
}

variable "container_registry_name" {

}

variable "container_registry_resource_group_name" {

}
