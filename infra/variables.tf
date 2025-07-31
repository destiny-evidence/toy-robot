variable "robot_name" {
  description = "Name of the robot."
}

variable "robot_id" {
  description = "The id the robot will send to destiny repository to identify itself."
}

variable "robot_secret" {
  description = "The secret the robot will use in HMAC auth with destiny repository."
  sensitive   = true
}

variable "destiny_repository_url" {
  description = "Url to configure the robot to post callbacks to."
}

# Variables below this line are for deploying the toy robot
# These may not be necessary for your use case
variable "container_registry_name" {
  description = "Name of the container registry where toy robot images are pushed."

}

variable "container_registry_resource_group_name" {
  description = "Name of the container registry resource group."
}

variable "environment" {
  description = "Environment for the toy robot, should be either development or staging."
  default     = "staging"
}


# Config variables for github actions
# These may not be necessary for your case
variable "github_repo" {
  description = "The github repository of the toy-robot"
  default     = "destiny-evidence/toy-robot"
}

variable "github_app_id" {
  description = "The app id for GitHub app used to configure github"
  type        = string
}

variable "github_app_installation_id" {
  description = "The app installation ID for the GitHub App used to configure github"
  type        = string
}

variable "github_app_pem" {
  description = "The app pem file for authenticating as a GitHub App"
  type        = string
  sensitive   = true
}
