# Infrastructure as Code – Azure (Terraform)

This folder provisions the cloud infrastructure for **HelpDesk Pro** on Microsoft Azure using Terraform.
It is the Infrastructure-as-Code deliverable of Activity 7 (CI/CD and IaC, delivered in English).

## Architecture

```text
                Internet (HTTPS)
                       │
        ┌──────────────▼───────────────┐
        │  Container App: frontend     │  React + Nginx, public ingress, 1..3 replicas
        └──────────────┬───────────────┘
                       │ http://helpdesk-dev-backend (internal)
        ┌──────────────▼───────────────┐
        │  Container App: backend      │  Flask + Gunicorn, internal ingress,
        │  autoscale 1..5 replicas     │  scales on HTTP concurrency
        └───────┬──────────────┬───────┘
                │ SSL          │ TLS (optional)
   ┌────────────▼─────┐   ┌────▼──────────────┐
   │ PostgreSQL       │   │ Azure Cache for   │
   │ Flexible Server  │   │ Redis             │
   └──────────────────┘   └───────────────────┘
        All containers send logs to a Log Analytics Workspace
```

| Resource | Azure service | Cloud model |
|---|---|---|
| `azurerm_container_app_environment` + 2 `azurerm_container_app` | Azure Container Apps | **PaaS** (serverless containers) |
| `azurerm_postgresql_flexible_server` | Azure Database for PostgreSQL | **PaaS** (managed database) |
| `azurerm_redis_cache` (optional) | Azure Cache for Redis | **PaaS** |
| `azurerm_log_analytics_workspace` | Azure Monitor Logs | **SaaS**-style monitoring |

## Why Terraform?

- **Declarative and reproducible:** the same code creates identical dev/staging/prod environments.
- **Plan before apply:** `terraform plan` shows exactly what will change before touching the cloud.
- **Versioned with the application:** infrastructure changes go through Git, pull requests and CI.
- **Cloud-agnostic tooling:** the same workflow works for AWS or GCP by switching providers.

## Files

| File | Purpose |
|---|---|
| `versions.tf` | Terraform and provider versions, optional remote state backend |
| `variables.tf` | Inputs with descriptions, defaults and validation rules |
| `main.tf` | All Azure resources |
| `outputs.tf` | Public URL, Swagger URL, database host, resource group |
| `terraform.tfvars.example` | Template for your own `terraform.tfvars` (never committed) |

## Usage

Prerequisites: [Terraform ≥ 1.6](https://developer.hashicorp.com/terraform/install), [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and an Azure subscription (Azure for Students works).

```powershell
az login
cd terraform
copy terraform.tfvars.example terraform.tfvars   # then edit the values
terraform init        # download the azurerm provider
terraform fmt         # format the code
terraform validate    # static validation
terraform plan        # preview the changes
terraform apply       # create the infrastructure (~10 minutes)
terraform output frontend_url
```

To remove everything and stop all costs:

```powershell
terraform destroy
```

## CI/CD integration

The `deploy-azure` job in `.github/workflows/ci-cd.yml` runs `terraform plan` and `terraform apply` automatically on the `main` branch when:

1. The repository variable `AZURE_DEPLOY` is set to `true`.
2. These repository secrets exist: `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID` (service principal), `DB_ADMIN_PASSWORD`, `JWT_SECRET_KEY` and `APP_ADMIN_PASSWORD`.

The images deployed are the ones that the same pipeline pushed to GitHub Container Registry, tagged with the commit SHA.

Create the service principal with:

```powershell
az ad sp create-for-rbac --name helpdesk-github --role Contributor --scopes /subscriptions/<SUBSCRIPTION_ID>
```

## Security notes

- Secrets are marked `sensitive = true`, so Terraform never prints them in logs.
- Secret values are stored as Container Apps secrets, not as plain environment variables.
- The backend has **internal** ingress only; just the frontend is exposed to the internet.
- PostgreSQL requires SSL (`sslmode=require`).
- `terraform.tfvars` and `*.tfstate` are excluded by `.gitignore`, because the state file can contain secrets.
