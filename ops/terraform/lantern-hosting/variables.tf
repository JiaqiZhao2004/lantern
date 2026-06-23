variable "aws_region" {
  description = "Primary AWS region for Lantern hosting resources."
  type        = string
}

variable "cloudflare_zone_name" {
  description = "Existing Cloudflare DNS zone that owns the Lantern frontend hostname."
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID used for Zero Trust Access resources."
  type        = string

  validation {
    condition     = length(trimspace(var.cloudflare_account_id)) > 0
    error_message = "cloudflare_account_id must be set to the Cloudflare account that owns Lantern Zero Trust Access."
  }
}

variable "frontend_domain_name" {
  description = "Public Lantern frontend hostname."
  type        = string
}

variable "frontend_bucket_name" {
  description = "Private S3 bucket that stores the built frontend assets."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository allowed to assume the Lantern frontend deploy role."
  type        = string
}

variable "deploy_branch" {
  description = "Git branch allowed to assume the Lantern frontend deploy role."
  type        = string
}

variable "tags" {
  description = "Additional tags applied to Lantern hosting resources."
  type        = map(string)
  default     = {}
}
