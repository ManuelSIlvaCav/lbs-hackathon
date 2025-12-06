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

variable "postgres_identifier" {
  type = string
}

variable "postgres_user_name" {
  type = string
}

variable "postgres_db_name" {
  type = string
}

variable "postgres_db_password" {
  type = string
}

variable "postgres_port" {
  type    = number
  default = 5432
}


variable "bastion_sg_id" {
  type    = string
  default = null
}
