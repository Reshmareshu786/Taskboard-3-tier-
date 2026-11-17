resource "azurerm_container_registry" "this" {
  name                = var.name # Alphanumeric only, globally unique
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  admin_enabled       = false
  tags                = var.tags
}