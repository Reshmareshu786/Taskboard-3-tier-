output "resource_group_name" { value = module.resource_group.name }
output "acr_login_server" { value = module.acr.login_server }
output "aks_cluster_name" { value = module.aks.cluster_name }
output "key_vault_name" { value = module.key_vault.name }
output "kv_secrets_provider_client_id" { value = module.aks.kv_secrets_provider_client_id }
output "postgres_fqdn" { value = module.postgresql.fqdn }