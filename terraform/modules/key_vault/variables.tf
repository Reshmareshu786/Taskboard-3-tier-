variable "name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "secret_names" {
  type    = set(string)
  default = []
}
variable "secret_values" {
  type      = map(string)
  sensitive = true
  default   = {}
}
variable "tags" {
  type    = map(string)
  default = {}
}