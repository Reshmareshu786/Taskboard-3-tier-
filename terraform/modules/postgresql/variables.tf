variable "server_name" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "vnet_id" { type = string }
variable "delegated_subnet_id" { type = string }
variable "admin_username" { type = string }
variable "admin_password" {
  type      = string
  sensitive = true
}
variable "database_name" {
  type    = string
  default = "taskboard"
}
variable "tags" {
  type    = map(string)
  default = {}
}