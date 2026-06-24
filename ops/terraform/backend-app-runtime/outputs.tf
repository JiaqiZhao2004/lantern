output "app_runtime_user_name" {
  description = "IAM user name for the backend app runtime KMS identity."
  value       = aws_iam_user.app_runtime.name
}

output "app_runtime_access_key_id" {
  description = "AWS access key ID for the backend app runtime identity."
  value       = aws_iam_access_key.app_runtime.id
}

output "app_runtime_secret_access_key" {
  description = "AWS secret access key for the backend app runtime identity."
  value       = aws_iam_access_key.app_runtime.secret
  sensitive   = true
}

output "backend_app_kms_key_id" {
  description = "Raw KMS key ID for the backend app envelope encryption key."
  value       = aws_kms_key.backend_app.key_id
}

output "backend_app_kms_key_arn" {
  description = "KMS key ARN for the backend app envelope encryption key."
  value       = aws_kms_key.backend_app.arn
}

output "backend_app_kms_alias_name" {
  description = "KMS alias name to use as KMS_KEY_ID in backend.env."
  value       = aws_kms_alias.backend_app.name
}
