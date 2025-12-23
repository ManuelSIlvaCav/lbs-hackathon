


## Application environment variables
variable "mongodb_domain" {
  type      = string
  sensitive = true
}

variable "mongodb_user" {
  type      = string
  sensitive = true
}

variable "mongodb_password" {
  type      = string
  sensitive = true
}

variable "mongodb_database" {
  type    = string
  default = "lbs_hackathon"
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "apollo_api_key" {
  type      = string
  sensitive = true
}

## SSL Certificate
variable "certificate_arn" {
  type        = string
  description = "ARN of the SSL certificate for HTTPS listener"
  default     = "arn:aws:acm:eu-west-1:142939271009:certificate/721c6dd7-c62e-488f-9622-dacc81c938a1"
}
