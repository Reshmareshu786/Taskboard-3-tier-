output "cluster_name" { value = azurerm_kubernetes_cluster.this.name }
output "kv_secrets_provider_client_id" {
  value = azurerm_kubernetes_cluster.this.key_vault_secrets_provider[0].secret_identity[0].client_id
}