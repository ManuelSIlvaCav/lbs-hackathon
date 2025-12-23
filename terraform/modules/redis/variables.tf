variable "environment" {
  type = string
}

variable "service_name" {
  type    = string
  default = "apply-ai"
}


variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}


variable "ecs_sg_id" {
  type    = string
  default = null
}

variable "bastion_sg_id" {
  type    = string
  default = null
}
