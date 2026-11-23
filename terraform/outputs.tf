# -----------------------------------------------------------------------------
# Outputs shown after "terraform apply"
# -----------------------------------------------------------------------------
output "frontend_url" {
  description = "Public URL of the HelpDesk Pro web application."
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "api_docs_url" {
  description = "Swagger UI served through the frontend proxy."
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}/api/docs"
}

output "backend_internal_fqdn" {
  description = "Internal hostname of the backend (not reachable from the internet)."
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "postgres_fqdn" {
  description = "Hostname of the managed PostgreSQL server."
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "resource_group" {
  description = "Resource group that contains every resource (delete it to remove everything)."
  value       = azurerm_resource_group.main.name
}

output "log_analytics_workspace_id" {
  description = "Workspace where container logs can be queried with KQL."
  value       = azurerm_log_analytics_workspace.main.workspace_id
}
