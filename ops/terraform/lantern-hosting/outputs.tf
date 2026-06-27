output "frontend_bucket_names" {
  description = "S3 bucket names keyed by environment for the Lantern frontend deploy workflow."
  value = {
    for env_name, bucket in aws_s3_bucket.frontend :
    env_name => bucket.bucket
  }
}

output "cloudfront_distribution_ids" {
  description = "CloudFront distribution IDs keyed by environment name."
  value = {
    for env_name, distribution in aws_cloudfront_distribution.frontend :
    env_name => distribution.id
  }
}

output "cloudfront_distribution_domain_names" {
  description = "CloudFront hostnames keyed by environment name."
  value = {
    for env_name, distribution in aws_cloudfront_distribution.frontend :
    env_name => distribution.domain_name
  }
}

output "github_actions_frontend_deploy_role_arn" {
  description = "IAM role ARN for the GitHub Actions frontend deploy workflow."
  value       = aws_iam_role.github_actions_frontend_deploy.arn
}

output "frontend_acm_certificate_arn" {
  description = "ACM certificate ARN for the Lantern frontend domain."
  value       = aws_acm_certificate_validation.frontend.certificate_arn
}
