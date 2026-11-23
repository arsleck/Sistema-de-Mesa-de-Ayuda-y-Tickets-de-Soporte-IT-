# -----------------------------------------------------------------------------
# HelpDesk Pro - Azure infrastructure (Activity 7: Infrastructure as Code)
#
#   Resource Group
#   ├── Log Analytics Workspace      -> centralized container logs and metrics
#   ├── PostgreSQL Flexible Server   -> managed database (PaaS)
#   ├── Azure Cache for Redis        -> shared rate-limit storage (optional)
#   └── Container Apps Environment   -> serverless containers (PaaS)
#       ├── backend  (internal ingress, autoscaled 1..N by HTTP concurrency)
#       └── frontend (public HTTPS ingress, Nginx proxy to the backend)
# -----------------------------------------------------------------------------

locals {
  prefix = "${var.project_name}-${var.environment}"
  tags = merge({
    project     = "HelpDesk Pro"
    environment = var.environment
    managed_by  = "terraform"
  }, var.tags)

  # Name of the backend app; the frontend Nginx reaches it at http://<name> inside the environment
  backend_app_name         = "${local.prefix}-backend"
  use_registry_credentials = var.registry_username != ""

  database_url = format(
    "postgresql://%s:%s@%s:5432/%s?sslmode=require",
    var.db_admin_username,
    urlencode(var.db_admin_password),
    azurerm_postgresql_flexible_server.main.fqdn,
    azurerm_postgresql_flexible_server_database.app.name,
  )

  ratelimit_storage_uri = var.enable_redis ? format(
    "rediss://:%s@%s:%d/0",
    azurerm_redis_cache.main[0].primary_access_key,
    azurerm_redis_cache.main[0].hostname,
    azurerm_redis_cache.main[0].ssl_port,
  ) : "memory://"
}

# Random suffix for resources whose name must be globally unique
resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

# -----------------------------------------------------------------------------
# Resource group
# -----------------------------------------------------------------------------
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}

# -----------------------------------------------------------------------------
# Observability: every container writes its stdout (JSON logs) here
# -----------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

# -----------------------------------------------------------------------------
# Database: Azure Database for PostgreSQL Flexible Server
# -----------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server" "main" {
  name                          = "psql-${local.prefix}-${random_string.suffix.result}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  version                       = "16"
  sku_name                      = "B_Standard_B1ms" # smallest burstable tier (low cost)
  storage_mb                    = 32768
  backup_retention_days         = 7
  administrator_login           = var.db_admin_username
  administrator_password        = var.db_admin_password
  public_network_access_enabled = true
  tags                          = local.tags

  lifecycle {
    ignore_changes = [zone] # Azure may pick the availability zone
  }
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "mesa_ayuda_it"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# 0.0.0.0 - 0.0.0.0 is Azure's convention for "allow traffic from Azure services"
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# -----------------------------------------------------------------------------
# Optional Redis: shares the login rate-limit counters between backend replicas
# -----------------------------------------------------------------------------
resource "azurerm_redis_cache" "main" {
  count                = var.enable_redis ? 1 : 0
  name                 = "redis-${local.prefix}-${random_string.suffix.result}"
  location             = azurerm_resource_group.main.location
  resource_group_name  = azurerm_resource_group.main.name
  capacity             = 0
  family               = "C"
  sku_name             = "Basic"
  minimum_tls_version  = "1.2"
  non_ssl_port_enabled = false
  tags                 = local.tags
}

# -----------------------------------------------------------------------------
# Container Apps environment (managed Kubernetes-based serverless platform)
# -----------------------------------------------------------------------------
resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.prefix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.tags
}

# -----------------------------------------------------------------------------
# Backend: Flask API (internal only, reachable from the frontend)
# -----------------------------------------------------------------------------
resource "azurerm_container_app" "backend" {
  name                         = local.backend_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  # Secrets are stored encrypted by Azure and injected as environment variables
  secret {
    name  = "database-url"
    value = local.database_url
  }
  secret {
    name  = "jwt-secret-key"
    value = var.jwt_secret_key
  }
  secret {
    name  = "admin-password"
    value = var.admin_password
  }
  secret {
    name  = "ratelimit-storage-uri"
    value = local.ratelimit_storage_uri
  }

  dynamic "secret" {
    for_each = local.use_registry_credentials ? [1] : []
    content {
      name  = "registry-password"
      value = var.registry_password
    }
  }

  dynamic "registry" {
    for_each = local.use_registry_credentials ? [1] : []
    content {
      server               = var.registry_server
      username             = var.registry_username
      password_secret_name = "registry-password"
    }
  }

  ingress {
    external_enabled = false # not exposed to the internet: only the frontend calls it
    target_port      = 5000
    transport        = "http"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    # Horizontal autoscaling: one extra replica for every 20 concurrent requests
    http_scale_rule {
      name                = "http-concurrency"
      concurrent_requests = "20"
    }

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
      env {
        name        = "JWT_SECRET_KEY"
        secret_name = "jwt-secret-key"
      }
      env {
        name        = "ADMIN_PASSWORD"
        secret_name = "admin-password"
      }
      env {
        name        = "RATELIMIT_STORAGE_URI"
        secret_name = "ratelimit-storage-uri"
      }
      env {
        name  = "ADMIN_USERNAME"
        value = "admin_soporte"
      }
      env {
        name  = "TRUST_PROXY"
        value = "1"
      }
      env {
        name  = "CORS_ORIGINS"
        value = "https://${local.prefix}-frontend.${azurerm_container_app_environment.main.default_domain}"
      }

      liveness_probe {
        transport = "HTTP"
        port      = 5000
        path      = "/health"
      }
      readiness_probe {
        transport = "HTTP"
        port      = 5000
        path      = "/health"
      }
    }
  }
}

# -----------------------------------------------------------------------------
# Frontend: React + Nginx (public HTTPS endpoint)
# -----------------------------------------------------------------------------
resource "azurerm_container_app" "frontend" {
  name                         = "${local.prefix}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  dynamic "secret" {
    for_each = local.use_registry_credentials ? [1] : []
    content {
      name  = "registry-password"
      value = var.registry_password
    }
  }

  dynamic "registry" {
    for_each = local.use_registry_credentials ? [1] : []
    content {
      server               = var.registry_server
      username             = var.registry_username
      password_secret_name = "registry-password"
    }
  }

  ingress {
    external_enabled = true # public URL with a managed TLS certificate
    target_port      = 80
    transport        = "auto"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = 0.25
      memory = "0.5Gi"

      # Nginx template variable: where /api and /health are proxied to
      env {
        name  = "BACKEND_URL"
        value = "http://${azurerm_container_app.backend.name}"
      }
    }
  }
}
