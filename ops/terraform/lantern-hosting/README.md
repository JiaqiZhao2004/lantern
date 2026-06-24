# Lantern Hosting Terraform

This stack provisions Lantern's production frontend hosting baseline:

- a private S3 bucket for built frontend assets
- a CloudFront distribution with Origin Access Control
- a CloudFront Function that rewrites extensionless SPA routes to `/index.html`
- an ACM certificate in `us-east-1` for `lantern.royzhao.dev`
- Cloudflare DNS records for ACM validation and the frontend hostname
- CloudFront `/api/*` routing to the Cloudflare Access-protected backend origin
- a Cloudflare Access application, policy, and service token for `lantern-api.royzhao.dev`
- a dedicated GitHub Actions OIDC deploy role for this repository

## State backend

Terraform state is stored in the existing shared S3 bucket:

- bucket: `terraform-state-royzhao`
- key: `lantern/frontend-hosting/terraform.tfstate`
- region: `us-east-2`

## Prerequisites

Set these environment variables before running Terraform:

```bash
export CLOUDFLARE_API_TOKEN=...
```

The Cloudflare API token needs permission to manage both DNS and Zero Trust Access resources for this stack:

- `Zone:DNS:Edit` for `royzhao.dev`
- `Account:Access: Apps and Policies:Edit`
- `Account:Access: Service Tokens:Edit`

If using the local `.env` file, export its values before running Terraform:

```bash
set -a
source .env
set +a
```

Use your usual AWS credentials locally, for example through `AWS_PROFILE`, `aws sso login`, or environment variables.

The GitHub OIDC trust is scoped to the renamed repository path: `JiaqiZhao2004/lantern`.
Set `cloudflare_account_id` in `terraform.tfvars` to the Cloudflare account that owns the Zero Trust Access configuration.

The Cloudflare Access service token secret is stored in Terraform state and copied into CloudFront as origin custom headers. Keep the token scoped to the backend origin and rotate it if exposed.

## API edge behavior

The `/api/*` CloudFront behavior routes production browser API traffic from `lantern.royzhao.dev` to the tunnel-backed backend origin at `lantern-api.royzhao.dev`.

It should:

- preserve the full viewer request URI without rewriting `/api`
- allow `GET`, `HEAD`, `OPTIONS`, `PUT`, `POST`, `PATCH`, and `DELETE`
- disable caching
- forward all query strings
- forward the `Authorization` header
- avoid forwarding cookies unless the backend gains a cookie-based need

Do not expand production CORS for this path. The browser-facing production API is same-origin through `lantern.royzhao.dev`, so CORS should stay limited to the local development path unless a real cross-origin workflow is introduced later.

Apply Cloudflare Access protection and CloudFront `/api/*` routing together. Access-first breaks the direct proof endpoint before CloudFront can use it, and CloudFront-first leaves the origin publicly reachable longer than necessary.

Required validation after apply:

- direct unauthenticated requests to `https://lantern-api.royzhao.dev/health/ready` are blocked by Cloudflare Access
- CloudFront can reach the backend origin through the Access service token
- `https://lantern.royzhao.dev/api/v1/...` reaches the backend through CloudFront
- an authenticated production API request succeeds with a Firebase bearer token

## Apply

```bash
cd ops/terraform/lantern-hosting
terraform init
terraform plan
terraform apply
```

## GitHub repository variables

After apply, set these repository variables for `.github/workflows/deploy-frontend.yml`:

- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `FRONTEND_S3_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID`

Their values come from this stack's outputs:

```bash
terraform output -raw github_actions_frontend_deploy_role_arn
terraform output -raw frontend_bucket_name
terraform output -raw cloudfront_distribution_id
```
