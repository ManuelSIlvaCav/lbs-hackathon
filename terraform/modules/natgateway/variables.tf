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

variable "enable_nat_gateway" {
  type    = bool
  default = true
}