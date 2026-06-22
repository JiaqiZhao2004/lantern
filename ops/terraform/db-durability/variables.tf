variable "aws_region" {
  description = "AWS region for Lantern durability resources."
  type        = string
}

variable "backup_bucket_name" {
  description = "Private S3 bucket that stores Lantern database backups."
  type        = string
}

variable "backup_upload_user_name" {
  description = "IAM user name for the Lantern backup uploader."
  type        = string
}

variable "six_hourly_prefix" {
  description = "S3 prefix used for short-retention recovery points."
  type        = string
  default     = "postgres/six-hourly"
}

variable "weekly_prefix" {
  description = "S3 prefix used for weekly recovery points."
  type        = string
  default     = "postgres/weekly"
}

variable "tags" {
  description = "Additional tags applied to Lantern durability resources."
  type        = map(string)
  default     = {}
}
