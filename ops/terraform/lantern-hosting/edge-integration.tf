locals {
  backend_origin_ids = {
    for env_name in keys(var.backend_origin_domain_names) :
    env_name => "lantern-${env_name}-backend-origin"
  }
}

data "aws_cloudfront_cache_policy" "api_caching_disabled" {
  name = "Managed-CachingDisabled"
}

resource "aws_cloudfront_origin_request_policy" "api" {
  name    = "lantern-api-origin-request"
  comment = "Forward the headers and parameters Lantern API requests need."

  cookies_config {
    cookie_behavior = "none"
  }

  headers_config {
    header_behavior = "whitelist"

    headers {
      items = ["Authorization"]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "cloudflare_zero_trust_access_service_token" "backend_origin" {
  account_id = var.cloudflare_account_id
  name       = "lantern-cloudfront-backend-origin"
  duration   = "8760h"
}

resource "cloudflare_zero_trust_access_policy" "backend_origin" {
  account_id = var.cloudflare_account_id
  name       = "Allow Lantern CloudFront backend origin"
  decision   = "non_identity"

  include = [{
    service_token = {
      token_id = cloudflare_zero_trust_access_service_token.backend_origin.id
    }
  }]
}

resource "cloudflare_zero_trust_access_application" "backend_origin" {
  for_each = var.backend_origin_domain_names

  account_id                = var.cloudflare_account_id
  name                      = "Lantern ${title(each.key)} Backend Origin"
  type                      = "self_hosted"
  domain                    = each.value
  service_auth_401_redirect = true
  session_duration          = "24h"

  policies = [{
    id         = cloudflare_zero_trust_access_policy.backend_origin.id
    precedence = 1
  }]
}
