variable "vnet_name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "address_space" {
  type    = list(string)
  default = ["10.0.0.0/16"]
}
variable "aks_subnet_prefix" {
  type    = string
  default = "10.0.1.0/24"
}
variable "postgres_subnet_prefix" {
  type    = string
  default = "10.0.2.0/24"
}
variable "tags" {
  type    = map(string)
  default = {}
}