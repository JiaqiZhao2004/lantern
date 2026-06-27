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

variable "frontend_domain_names" {
  description = "Public Lantern frontend hostnames keyed by environment name."
  type        = map(string)

  validation {
    condition = alltrue([
      contains(keys(var.frontend_domain_names), "production"),
      contains(keys(var.frontend_domain_names), "public"),
    ])
    error_message = "frontend_domain_names must include at least the production and public hostnames."
  }
}

variable "backend_origin_domain_names" {
  description = "Tunnel-backed backend origin hostnames keyed by environment name."
  type        = map(string)

  validation {
    condition = alltrue([
      contains(keys(var.backend_origin_domain_names), "production"),
      contains(keys(var.backend_origin_domain_names), "public"),
    ])
    error_message = "backend_origin_domain_names must include at least the production and public origin hostnames."
  }
}

variable "frontend_bucket_names" {
  description = "Private S3 bucket names keyed by frontend environment."
  type        = map(string)

  validation {
    condition = alltrue([
      contains(keys(var.frontend_bucket_names), "production"),
      contains(keys(var.frontend_bucket_names), "public"),
    ])
    error_message = "frontend_bucket_names must include at least the production and public bucket names."
  }
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
