terraform {
  required_version = ">= 1.6.0"

  backend "s3" {
    bucket  = "terraform-state-royzhao"
    key     = "lantern/backend-app-runtime/terraform.tfstate"
    region  = "us-east-2"
    encrypt = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
