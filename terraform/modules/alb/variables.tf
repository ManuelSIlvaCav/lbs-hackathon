variable "environment" {
  type    = string
  default = "dev"
}

variable "container_port" {
  type    = number
  default = 3000
}

variable "service_name" {
  type    = string
  default = "apply-ai"
}


variable "healthcheck_matcher" {
  type    = string
  default = "200"
}

variable "healthcheck_endpoint" {
  type    = string
  default = "/healthcheck"
}


## Imported from other modules
variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

## SSL Certificate
variable "certificate_arn" {
  type        = string
  description = "ARN of the SSL certificate for HTTPS listener"
  default     = "arn:aws:acm:eu-west-1:142939271009:certificate/721c6dd7-c62e-488f-9622-dacc81c938a1"
}
