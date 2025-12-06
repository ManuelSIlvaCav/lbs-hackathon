variable "environment" {
  type = string
}

variable "availability_zone_names" {
  type    = list(string)
  default = ["eu-west-1a", "eu-west-1b"]
}

variable "vpc_main_id" {
  type = string
}

variable "public_subnets_ids" {
  type    = list(string)
}

variable "vpc_cidr" {
  type    = string
  default = "172.17.0.0/16"
}

variable "private_route_table_ids" {
  type = list(string)
}

# Bastion functionality - SSH key name
variable "ssh_key_name" {
  type = string
}