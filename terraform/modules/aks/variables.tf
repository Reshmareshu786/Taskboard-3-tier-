variable "cluster_name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "dns_prefix" { type = string }
variable "aks_subnet_id" { type = string }
variable "acr_id" { type = string }
variable "key_vault_id" { type = string }
variable "node_count" {
  type    = number
  default = 2
}
variable "vm_size" {
  type    = string
  default = "Standard_B2s"
}
variable "tags" {
  type    = map(string)
  default = {}
}