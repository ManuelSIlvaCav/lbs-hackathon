variable "environment" {
  type    = string
  default = "prod"
}

variable "service_name" {
  type    = string
  default = "apply-ai"
}

variable "ecs_task_desired_count" {
  type    = number
  default = 1
}

variable "ecs_task_deployment_minimum_healthy_percent" {
  type    = number
  default = 50
}

variable "ecs_task_deployment_maximum_percent" {
  type    = number
  default = 100
}

variable "container_port" {
  type    = number
  default = 3000
}


variable "cpu_units" {
  type    = number
  default = 256
}

variable "memory" {
  type    = number
  default = 512
}

variable "ecr_container_hash" {
  type    = string
  default = "latest"
}

variable "logs_region" {
  type    = string
  default = "eu-west-1"
}

variable "tag" {
  type    = string
  default = "latest"
}

## Imported from other modules

## VPC related variables
variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

## New variables for ALB integration

variable "alb_security_group_id" {
  type = string
}

variable "alb_target_group_arn" {
  type = string
}

variable "ecs_sg_id" {
  type = string
}


## ECR related variables
variable "ecr_repository_url" {
  type = string
}


