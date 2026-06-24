variable "aws_region" {
  description = "AWS region for Lantern backend app runtime resources."
  type        = string
}

variable "app_runtime_user_name" {
  description = "IAM user name for the backend app runtime KMS identity."
  type        = string
}

variable "kms_alias_name" {
  description = "KMS alias used by the backend app for Plaid access-token envelope encryption."
  type        = string

  validation {
    condition     = startswith(var.kms_alias_name, "alias/")
    error_message = "kms_alias_name must start with alias/."
  }
}

variable "tags" {
  description = "Additional tags applied to Lantern backend app runtime resources."
  type        = map(string)
  default     = {}
}
