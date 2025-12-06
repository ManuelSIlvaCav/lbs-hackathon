terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.2.0"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "eu-west-1"
  default_tags {
    tags = {
      Environment = "prod",
      Project     = "apply-ai",
    }
  }
}

