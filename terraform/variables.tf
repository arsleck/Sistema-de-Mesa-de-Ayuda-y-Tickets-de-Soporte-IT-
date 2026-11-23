# -----------------------------------------------------------------------------
# Input variables
# Sensitive values are passed with TF_VAR_* environment variables or a
# terraform.tfvars file that is NEVER committed (see terraform.tfvars.example).
# -----------------------------------------------------------------------------
variable "project_name" {
  description = "Short name used as a prefix for every resource."
  type        = string
  default     = "helpdesk"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging or prod."
  }
}

variable "location" {
  description = "Azure region. eastus2 usually allows Azure for Students subscriptions."
  type        = string
  default     = "eastus2"
}

variable "backend_image" {
  description = "Full backend image reference, e.g. ghcr.io/<owner>/helpdesk-backend:<tag>."
  type        = string
}

variable "frontend_image" {
  description = "Full frontend image reference, e.g. ghcr.io/<owner>/helpdesk-frontend:<tag>."
  type        = string
}

variable "registry_server" {
  description = "Container registry that hosts the images."
  type        = string
  default     = "ghcr.io"
}

variable "registry_username" {
  description = "Registry user (only needed when the images are private)."
  type        = string
  default     = ""
}

variable "registry_password" {
  description = "Registry token (only needed when the images are private)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_admin_username" {
  description = "PostgreSQL administrator user."
  type        = string
  default     = "helpdeskadmin"
}

variable "db_admin_password" {
  description = "PostgreSQL administrator password."
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Secret used to sign JWT tokens (32+ characters)."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.jwt_secret_key) >= 32
    error_message = "jwt_secret_key must be at least 32 characters long."
  }
}

variable "admin_password" {
  description = "Password of the initial HelpDesk admin user (admin_soporte)."
  type        = string
  sensitive   = true
}

variable "backend_min_replicas" {
  description = "Minimum number of backend replicas (high availability)."
  type        = number
  default     = 1
}

variable "backend_max_replicas" {
  description = "Maximum number of backend replicas (horizontal scalability)."
  type        = number
  default     = 5
}

variable "enable_redis" {
  description = "Provision Azure Cache for Redis to share the login rate limit across replicas."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Extra tags added to every resource."
  type        = map(string)
  default     = {}
}
