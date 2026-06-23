# Cloudflare Access Protected Backend Origin

Lantern's same-origin production API route will keep `lantern-api.royzhao.dev` as the CloudFront backend origin, but protect that hostname with Cloudflare Access so ordinary public requests do not reach the backend. CloudFront will authenticate to the origin with Cloudflare Access service-token headers stored in Terraform-managed CloudFront origin configuration, accepting that the narrowly scoped token secret also lives in Terraform state for this slice because it keeps the first same-origin cutover simple and repeatable while still closing direct public origin access.

The Cloudflare Access application, policy, and service token should be managed in the existing frontend hosting Terraform stack so the edge route and its origin protection are reviewed and applied together.
