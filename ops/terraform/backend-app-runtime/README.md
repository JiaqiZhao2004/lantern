# Lantern Backend App Runtime Terraform

This stack provisions the AWS runtime boundary used by the backend app containers:

- a KMS key and alias for Plaid access-token envelope encryption
- a narrow IAM user for the backend and worker containers
- an IAM policy that allows only KMS use for the app key
- an access key that is installed into the host-mounted app credentials file

The current runtime model is a generic Ubuntu host running Docker Compose. Because the
backend is not running on EC2 with an instance profile, the app credentials are installed
as a profile in the credentials file mounted by `ops/deployment/backend/app-stack/compose.yml`.

## State backend

Terraform state is stored in the existing shared S3 bucket:

- bucket: `terraform-state-royzhao`
- key: `lantern/backend-app-runtime/terraform.tfstate`
- region: `us-east-2`

## Prerequisites

Use your usual AWS credentials locally, for example through `AWS_PROFILE`,
`aws sso login --profile <profile> --no-browser --use-device-code`, or environment
variables.

## Apply

```bash
cd ops/terraform/backend-app-runtime
terraform init
terraform plan
terraform apply
```

## Runtime values

After apply, create the backend environment file on the server if it does not
already exist, then review the prefilled AWS runtime settings:

```bash
cd ops/deployment/backend/app-stack
test -f backend.env || cp backend.env.example backend.env
```

The example already contains the expected region, `lantern-app-kms` profile, and KMS
alias. Keep AWS credential secret values out of this file.

Install the backend app AWS credential into the host file referenced by
`AWS_SHARED_CREDENTIALS_PATH` in `ops/deployment/backend/app-stack/compose.env`:

```bash
test -f compose.env || cp compose.env.example compose.env

cd ops/terraform/backend-app-runtime
app_profile="lantern-app-kms"
credentials_path="/srv/lantern/secrets/aws-credentials"

install -m 700 -d "$(dirname "$credentials_path")"
install -m 600 /dev/null "$credentials_path"

AWS_SHARED_CREDENTIALS_FILE="$credentials_path" \
  aws configure set aws_access_key_id "$(terraform output -raw app_runtime_access_key_id)" \
  --profile "$app_profile"

AWS_SHARED_CREDENTIALS_FILE="$credentials_path" \
  aws configure set aws_secret_access_key "$(terraform output -raw app_runtime_secret_access_key)" \
  --profile "$app_profile"
```

The `backend` and `worker` containers mount this file read-only at `/run/aws/credentials`.
Do not reuse the backup-upload profile here; that identity is scoped to S3 backup writes.
