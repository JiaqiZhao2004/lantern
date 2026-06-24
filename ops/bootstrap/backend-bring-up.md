# Backend Host Bring-Up

This is the thin driver for bringing a Lantern backend host to a working state for either first deploy or replacement-host recovery. It coordinates other layer docs rather than duplicating them.

## Assumptions

- frontend hosting for `lantern.royzhao.dev` already exists
- the Ubuntu host already exists and you have operator SSH access

## Bring-up order

1. Prepare host prerequisites and install host-level packages (CLI commands provided at bottom):
   - common utilities for package installs and repo checkout
   - Terraform for repo-owned infrastructure stacks
   - Tailscale for private operator access
   - `cloudflared`
   - Docker Engine
   - Docker Compose plugin
   - AWS CLI
2. Apply the DB durability Terraform stack in [ops/terraform/db-durability/README.md](../terraform/db-durability/README.md).
3. Create the shared Docker network used by the app stack and observability stack:
   - `docker network create lantern-backend`
4. Enroll and configure the Cloudflare Tunnel in [ops/deployment/backend/tunnel/README.md](../deployment/backend/tunnel/README.md), but defer public-host validation until after the first app deploy.
5. Prepare and deploy the app stack from [ops/deployment/backend/app-stack/README.md](../deployment/backend/app-stack/README.md).
6. Activate the `cloudflared` service and complete tunnel validation using [ops/deployment/backend/tunnel/README.md](../deployment/backend/tunnel/README.md).
7. Enable the backup timers described in [ops/durability/backend/README.md](../durability/backend/README.md) only after the backend runtime is healthy enough for backups to succeed.
8. Bring up backend observability from [ops/observability/backend/README.md](../observability/backend/README.md).

## Notes

- The bootstrap layer stays intentionally thin. Component-specific commands live with their components.

## Host Prerequisites

Run these commands on a fresh Ubuntu LTS host before copying runtime env files or starting
Compose services.

### Base Utilities

```bash
sudo apt-get update
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  git \
  jq \
  lsb-release \
  unzip \
  vim
```

### Terraform

Install Terraform from HashiCorp's official Ubuntu `apt` repository:

```bash
wget -O - https://apt.releases.hashicorp.com/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt-get update
sudo apt-get install -y terraform
terraform version
```

### Tailscale

Install Tailscale for private operator access:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

After login, confirm the host has a Tailscale address:

```bash
tailscale status
tailscale ip -4
```

### Docker Engine And Compose Plugin

Install Docker from Docker's official Ubuntu `apt` repository:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

Allow the operator user to run Docker without `sudo`:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker version
docker compose version
```

If `newgrp docker` does not refresh the shell cleanly, log out and SSH back in.

### Cloudflare Tunnel Client

Install `cloudflared` from Cloudflare's package repository:

```bash
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list

sudo apt-get update
sudo apt-get install -y cloudflared
cloudflared --version
```

### AWS CLI

Install AWS CLI v2 if S3 backup upload is enabled:

```bash
tmp_dir="$(mktemp -d)"
cd "$tmp_dir"

case "$(uname -m)" in
  x86_64) aws_cli_arch="x86_64" ;;
  aarch64|arm64) aws_cli_arch="aarch64" ;;
  *) echo "Unsupported AWS CLI architecture: $(uname -m)" >&2; exit 1 ;;
esac

curl "https://awscli.amazonaws.com/awscli-exe-linux-${aws_cli_arch}.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

aws --version
```

After the DB durability Terraform stack creates `backup_upload_access_key_id` and
`backup_upload_secret_access_key`, store them outside the repo in a dedicated AWS CLI
profile as described in [ops/terraform/db-durability/README.md](../terraform/db-durability/README.md).
Then set that profile name in `ops/durability/backend/backup.env` with
`BACKUP_AWS_PROFILE`.

### Repository Checkout

Choose a host path for Lantern and clone or update the repo:

```bash
sudo mkdir -p /srv/lantern
sudo chown "$USER:$USER" /srv/lantern

git clone https://github.com/JiaqiZhao2004/lantern.git /srv/lantern
cd /srv/lantern
```

If the repo already exists on a replacement host, update it intentionally:

```bash
cd /srv/lantern
git fetch --all --prune
git status
```
