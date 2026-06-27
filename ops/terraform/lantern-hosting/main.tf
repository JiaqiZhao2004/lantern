locals {
  stack_name = "lantern-hosting"
  origin_id  = "lantern-frontend-s3"

  frontend_record_names = {
    for env_name, domain_name in var.frontend_domain_names :
    env_name => trimsuffix(domain_name, ".${var.cloudflare_zone_name}")
  }

  common_tags = merge(
    {
      ManagedBy = "terraform"
      Project   = "lantern"
      Stack     = local.stack_name
    },
    var.tags
  )

  acm_validation_records = {
    for option in aws_acm_certificate.frontend.domain_validation_options :
    option.domain_name => {
      name  = trimsuffix(option.resource_record_name, ".")
      type  = option.resource_record_type
      value = trimsuffix(option.resource_record_value, ".")
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect = "Allow"

    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/${var.deploy_branch}"]
    }
  }
}

data "aws_iam_policy_document" "github_actions_deploy" {
  statement {
    sid    = "ListFrontendBucket"
    effect = "Allow"

    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
    ]

    resources = [
      for bucket in aws_s3_bucket.frontend :
      bucket.arn
    ]
  }

  statement {
    sid    = "ManageFrontendObjects"
    effect = "Allow"

    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]

    resources = [
      for bucket in aws_s3_bucket.frontend :
      "${bucket.arn}/*"
    ]
  }

  statement {
    sid    = "InvalidateCloudFront"
    effect = "Allow"

    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetDistribution",
      "cloudfront:GetDistributionConfig",
    ]

    resources = [
      for distribution in aws_cloudfront_distribution.frontend :
      "arn:aws:cloudfront::${data.aws_caller_identity.current.account_id}:distribution/${distribution.id}"
    ]
  }
}

data "aws_iam_policy_document" "frontend_bucket" {
  for_each = var.frontend_bucket_names

  statement {
    sid    = "AllowCloudFrontReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = ["s3:GetObject"]

    resources = ["${aws_s3_bucket.frontend[each.key].arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend[each.key].arn]
    }
  }
}

data "cloudflare_zone" "frontend" {
  filter = {
    name = var.cloudflare_zone_name
  }
}

resource "aws_s3_bucket" "frontend" {
  for_each = var.frontend_bucket_names

  bucket = each.value
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  for_each = var.frontend_bucket_names

  bucket = aws_s3_bucket.frontend[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  for_each = var.frontend_bucket_names

  bucket = aws_s3_bucket.frontend[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  for_each = var.frontend_bucket_names

  bucket = aws_s3_bucket.frontend[each.key].id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_acm_certificate" "frontend" {
  provider    = aws.us_east_1
  domain_name = var.frontend_domain_names["production"]
  subject_alternative_names = [
    for env_name, domain_name in var.frontend_domain_names :
    domain_name if env_name != "production"
  ]
  validation_method = "DNS"
  tags              = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "cloudflare_dns_record" "acm_validation" {
  for_each = local.acm_validation_records

  zone_id = data.cloudflare_zone.frontend.id
  name    = each.value.name
  type    = each.value.type
  content = each.value.value
  ttl     = 1
  proxied = false
}

resource "aws_acm_certificate_validation" "frontend" {
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.frontend.arn

  validation_record_fqdns = [
    for option in aws_acm_certificate.frontend.domain_validation_options :
    trimsuffix(option.resource_record_name, ".")
  ]

  depends_on = [cloudflare_dns_record.acm_validation]
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "lantern-frontend-oac"
  description                       = "Origin access control for the Lantern frontend bucket."
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_response_headers_policy" "frontend" {
  name    = "lantern-frontend-security-headers"
  comment = "Security headers for the Lantern frontend."

  security_headers_config {
    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      override                   = true
      preload                    = true
    }

    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }
  }
}

resource "aws_cloudfront_function" "spa_rewrite" {
  name    = "lantern-spa-rewrite"
  runtime = "cloudfront-js-1.0"
  comment = "Serve index.html for extensionless Lantern app routes."
  publish = true
  code    = <<-EOT
    function handler(event) {
      var request = event.request;
      var uri = request.uri || "/";

      if (uri === "/" || uri.startsWith("/api/")) {
        return request;
      }

      var lastSegment = uri.split("/").pop();
      var hasExtension = lastSegment && lastSegment.indexOf(".") !== -1;

      if (!hasExtension) {
        request.uri = "/index.html";
      }

      return request;
    }
  EOT
}

resource "aws_cloudfront_distribution" "frontend" {
  for_each = var.frontend_domain_names

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Lantern ${each.key} frontend distribution."
  default_root_object = "index.html"
  aliases             = [each.value]
  price_class         = "PriceClass_100"
  tags                = local.common_tags

  origin {
    domain_name              = aws_s3_bucket.frontend[each.key].bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
    origin_id                = local.origin_id
  }

  origin {
    domain_name = var.backend_origin_domain_names[each.key]
    origin_id   = local.backend_origin_ids[each.key]

    custom_header {
      name  = "CF-Access-Client-Id"
      value = cloudflare_zero_trust_access_service_token.backend_origin.client_id
    }

    custom_header {
      name  = "CF-Access-Client-Secret"
      value = cloudflare_zero_trust_access_service_token.backend_origin.client_secret
    }

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true
    target_origin_id = local.origin_id

    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_rewrite.arn
    }

    response_headers_policy_id = aws_cloudfront_response_headers_policy.frontend.id
  }

  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    compress         = true
    target_origin_id = local.backend_origin_ids[each.key]

    viewer_protocol_policy     = "redirect-to-https"
    cache_policy_id            = data.aws_cloudfront_cache_policy.api_caching_disabled.id
    origin_request_policy_id   = aws_cloudfront_origin_request_policy.api.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.frontend.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.frontend.certificate_arn
    minimum_protocol_version = "TLSv1.2_2021"
    ssl_support_method       = "sni-only"
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  for_each = var.frontend_bucket_names

  bucket = aws_s3_bucket.frontend[each.key].id
  policy = data.aws_iam_policy_document.frontend_bucket[each.key].json

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

resource "cloudflare_dns_record" "frontend" {
  for_each = var.frontend_domain_names

  zone_id = data.cloudflare_zone.frontend.id
  name    = local.frontend_record_names[each.key]
  type    = "CNAME"
  content = aws_cloudfront_distribution.frontend[each.key].domain_name
  ttl     = 1
  proxied = false
}

resource "aws_iam_role" "github_actions_frontend_deploy" {
  name               = "GitHubActionsLanternFrontendDeploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_policy" "github_actions_frontend_deploy" {
  name   = "GitHubActionsLanternFrontendDeploy"
  policy = data.aws_iam_policy_document.github_actions_deploy.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "github_actions_frontend_deploy" {
  role       = aws_iam_role.github_actions_frontend_deploy.name
  policy_arn = aws_iam_policy.github_actions_frontend_deploy.arn
}
