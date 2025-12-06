variable "service_name" {
  type    = string
  default = "apply-ai"
}

variable "environment" {
  type    = string
  default = "prod"
}


## Imported from other modules
variable "ecr_repository_url" {
  type = string
}


