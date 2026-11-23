# -----------------------------------------------------------------------------
# Terraform and provider versions
# -----------------------------------------------------------------------------
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state (recommended for teams / CI). Uncomment and create the storage
  # account first, otherwise the state is kept locally in terraform.tfstate.
  # backend "azurerm" {
  #   resource_group_name  = "rg-helpdesk-tfstate"
  #   storage_account_name = "helpdesktfstate"
  #   container_name       = "tfstate"
  #   key                  = "helpdesk.tfstate"
  # }
}

provider "azurerm" {
  features {}
}
