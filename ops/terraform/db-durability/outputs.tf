output "backup_bucket_name" {
  description = "S3 bucket name used by the Lantern backup uploader."
  value       = aws_s3_bucket.backups.bucket
}

output "backup_upload_user_name" {
  description = "IAM user name for the Lantern backup uploader."
  value       = aws_iam_user.backup_upload.name
}

output "backup_upload_access_key_id" {
  description = "AWS access key ID for the Lantern backup uploader."
  value       = aws_iam_access_key.backup_upload.id
}

output "backup_upload_secret_access_key" {
  description = "AWS secret access key for the Lantern backup uploader."
  value       = aws_iam_access_key.backup_upload.secret
  sensitive   = true
}

output "six_hourly_backup_prefix" {
  description = "S3 prefix for short-retention Lantern backups."
  value       = trimsuffix(var.six_hourly_prefix, "/")
}

output "weekly_backup_prefix" {
  description = "S3 prefix for weekly-retention Lantern backups."
  value       = trimsuffix(var.weekly_prefix, "/")
}
