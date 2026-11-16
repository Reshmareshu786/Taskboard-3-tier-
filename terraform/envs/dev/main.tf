resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

resource "random_password" "pg_admin" {
  length  = 20
  special = false
}

locals {
  prefix = "${var.project}-${var.environment}"
  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}

module "resource_group" {
  source   = "../../modules/resource_group"
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}

module "vnet" {
  source              = "../../modules/vnet"
  vnet_name           = "vnet-${local.prefix}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  tags                = local.tags
}

module "acr" {
  source              = "../../modules/acr"
  name                = "acr${var.project}${var.environment}${random_string.suffix.result}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  tags                = local.tags
}

module "postgresql" {
  source              = "../../modules/postgresql"
  server_name         = "psql-${local.prefix}-${random_string.suffix.result}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  vnet_id             = module.vnet.vnet_id
  delegated_subnet_id = module.vnet.postgres_subnet_id
  admin_username      = "taskboard"
  admin_password      = random_password.pg_admin.result
  database_name       = "taskboard"
  tags                = local.tags
}

module "key_vault" {
  source              = "../../modules/key_vault"
  name                = "kv-${local.prefix}-${random_string.suffix.result}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  secret_names        = ["db-host", "db-name", "db-user", "db-password"]
  secret_values = {
    "db-host"     = module.postgresql.fqdn
    "db-name"     = module.postgresql.database_name
    "db-user"     = "taskboard"
    "db-password" = random_password.pg_admin.result
  }
  tags = local.tags
}

module "aks" {
  source              = "../../modules/aks"
  cluster_name        = "aks-${local.prefix}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  dns_prefix          = "${local.prefix}-aks"
  aks_subnet_id       = module.vnet.aks_subnet_id
  acr_id              = module.acr.id
  key_vault_id        = module.key_vault.id
  node_count          = var.aks_node_count
  vm_size             = var.aks_vm_size
  tags                = local.tags
}