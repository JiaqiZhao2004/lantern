terraform {
  required_version = ">= 1.6.0"

  backend "s3" {
    bucket  = "terraform-state-royzhao"
    key     = "lantern/frontend-hosting/terraform.tfstate"
    region  = "us-east-2"
    encrypt = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}
