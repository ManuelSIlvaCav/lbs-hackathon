variable "environment" {
  type    = string
  default = "prod"
}

variable "service_name" {
  type    = string
  default = "apply-ai"
}

variable "container_port" {
  type    = number
  default = 3000
}


## VPC related variables
variable "vpc_id" {
  type = string
}

variable "alb_security_group_id" {
  type = string
}
