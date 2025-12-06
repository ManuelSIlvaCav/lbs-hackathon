#Instance related
variable "instance_type" {
  description = "Instance type for the bastion host"
  type        = string
  default     = "t4g.nano"
}

#Project related
variable "service_name" {
  type    = string
  default = "apply-ai"
}

variable "environment" {
  type    = string
  default = "prod"
}


#Network related
variable "vpc_main_id" {
  type = string
}

variable "key_name" {
  description = "Name of the key pair for SSH access"
  type        = string
}

variable "public_subnets_ids" {
  type = list(string)
}

variable "availability_zone_names" {
  type    = list(string)
  default = ["eu-west-1a", "eu-west-1b"]
}
