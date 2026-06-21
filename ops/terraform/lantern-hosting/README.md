# Lantern Hosting Terraform

This stack provisions Lantern's production frontend hosting baseline:

- a private S3 bucket for built frontend assets
- a CloudFront distribution with Origin Access Control
- a CloudFront Function that rewrites extensionless SPA routes to `/index.html`
- an ACM certificate in `us-east-1` for `lantern.royzhao.dev`
- Cloudflare DNS records for ACM validation and the frontend hostname
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

Use your usual AWS credentials locally, for example through `AWS_PROFILE`, `aws sso login`, or environment variables.

The GitHub OIDC trust is scoped to the renamed repository path: `JiaqiZhao2004/lantern`.

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
