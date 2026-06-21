output "frontend_bucket_name" {
  description = "S3 bucket name used by the Lantern frontend deploy workflow."
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID used by the Lantern frontend deploy workflow."
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_distribution_domain_name" {
  description = "CloudFront hostname that Cloudflare points lantern.royzhao.dev at."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "github_actions_frontend_deploy_role_arn" {
  description = "IAM role ARN for the GitHub Actions frontend deploy workflow."
  value       = aws_iam_role.github_actions_frontend_deploy.arn
}

output "frontend_acm_certificate_arn" {
  description = "ACM certificate ARN for the Lantern frontend domain."
  value       = aws_acm_certificate_validation.frontend.certificate_arn
}
