terraform {
  backend "azurerm" {
    resource_group_name  = "rg-taskboard-tfstate"
    storage_account_name = "sttaskboardtfiwj569"
    container_name       = "tfstate"
    key                  = "taskboard-dev.tfstate"
  }
}