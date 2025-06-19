terraform {
  required_version = ">= 1.0"

  cloud {
    organization = "destiny-evidence"
    workspaces {
      name = "toy-robot-staging"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.28.0"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = "3.3.0"
    }

    github = {
      source  = "integrations/github"
      version = "6.6.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {
}

provider "github" {
  owner = "destiny-evidence"
  app_auth {
    id              = var.github_app_id
    installation_id = var.github_app_installation_id
    pem_file        = var.github_app_pem
  }
}
