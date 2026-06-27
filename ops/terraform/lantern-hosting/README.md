# Lantern Hosting Terraform

This stack provisions Lantern's production frontend hosting baseline:

- a private S3 bucket for each built frontend deployment, one for `production` and one for `public`
- two CloudFront distributions with Origin Access Control, one for `production` and one for `public`
- a CloudFront Function that rewrites extensionless SPA routes to `/index.html`
- an ACM certificate in `us-east-1` that covers both frontend hostnames
- Cloudflare DNS records for ACM validation and both frontend hostnames
- CloudFront `/api/*` routing to the Cloudflare Access-protected backend origins
- Cloudflare Access applications for `lantern-api.royzhao.dev` and `lantern-public-api.royzhao.dev`, plus one shared service token and policy for CloudFront origin access
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

## Frontend artifacts

The stack serves different frontend artifacts on two browser hostnames:

- `lantern.royzhao.dev` for `production`
- `lantern-public.royzhao.dev` for `public`

Each hostname gets its own S3 bucket and CloudFront distribution so the frontend build can diverge by deployment-specific `VITE_*` values without sharing object state.

## API edge behavior

Each CloudFront distribution keeps same-origin `/api/*` routing, but sends requests to a different tunnel-backed backend origin:

- `lantern.royzhao.dev/api/*` -> `lantern-api.royzhao.dev`
- `lantern-public.royzhao.dev/api/*` -> `lantern-public-api.royzhao.dev`

It should:

- preserve the full viewer request URI without rewriting `/api`
- allow `GET`, `HEAD`, `OPTIONS`, `PUT`, `POST`, `PATCH`, and `DELETE`
- disable caching
- forward all query strings
- forward the `Authorization` header
- avoid forwarding cookies unless the backend gains a cookie-based need

Do not expand production CORS for this path. Both browser-facing APIs stay same-origin through their respective frontend hostnames, so CORS should stay limited to the local development path unless a real cross-origin workflow is introduced later.

Apply Cloudflare Access protection and CloudFront `/api/*` routing together. Access-first breaks the direct proof endpoint before CloudFront can use it, and CloudFront-first leaves the origin publicly reachable longer than necessary.

Required validation after apply:

- direct unauthenticated requests to `https://lantern-api.royzhao.dev/health/ready` are blocked by Cloudflare Access
- direct unauthenticated requests to `https://lantern-public-api.royzhao.dev/health/ready` are blocked by Cloudflare Access
- both CloudFront distributions can reach their backend origins through the Access service token
- `https://lantern.royzhao.dev/api/v1/...` reaches the backend through CloudFront
- `https://lantern-public.royzhao.dev/api/v1/...` reaches the backend through CloudFront
- an authenticated production API request succeeds with a Firebase bearer token

## Apply

```bash
cd ops/terraform/lantern-hosting
terraform init
terraform plan
terraform apply
```

## GitHub Actions environments

After apply, set these GitHub Environment variables for `.github/workflows/deploy-frontend.yml`:

- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `FRONTEND_S3_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_IDS`
- `VITE_AUTH_MODE`
- `VITE_ACCESS_CONTACT`

Their values come from this stack's outputs:

```bash
terraform output -raw github_actions_frontend_deploy_role_arn
terraform output -json frontend_bucket_names
terraform output -json cloudfront_distribution_ids
```

Use one GitHub Environment per frontend deployment:

- `production`
- `public`

Recommended values:

- `production`
  - `AWS_REGION=<aws region>`
  - `AWS_ROLE_TO_ASSUME=<terraform output github_actions_frontend_deploy_role_arn>`
  - `FRONTEND_S3_BUCKET=<frontend_bucket_names.production>`
  - `CLOUDFRONT_DISTRIBUTION_IDS=<cloudfront_distribution_ids.production>`
  - `VITE_AUTH_MODE=restricted`
  - `VITE_ACCESS_CONTACT=Roy Zhao`

- `public`
  - `AWS_REGION=<aws region>`
  - `AWS_ROLE_TO_ASSUME=<terraform output github_actions_frontend_deploy_role_arn>`
  - `FRONTEND_S3_BUCKET=<frontend_bucket_names.public>`
  - `CLOUDFRONT_DISTRIBUTION_IDS=<cloudfront_distribution_ids.public>`
  - `VITE_AUTH_MODE=open`
  - `VITE_ACCESS_CONTACT=Roy Zhao`
