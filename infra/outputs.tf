output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "api_url" {
  description = "URL pública da API (use no vídeo de demonstração)"
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "search_endpoint" {
  value = "https://${azurerm_search_service.ai.name}.search.windows.net"
}

output "search_admin_key" {
  description = "Chave admin do AI Search — guardar em local seguro"
  value       = azurerm_search_service.ai.primary_key
  sensitive   = true
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "openai_api_key" {
  value     = azurerm_cognitive_account.openai.primary_access_key
  sensitive = true
}

output "openai_embedding_deployment" {
  value = azurerm_cognitive_deployment.embedding.name
}

output "openai_chat_deployment" {
  value = azurerm_cognitive_deployment.chat.name
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  value = azurerm_container_registry.acr.admin_username
}

output "acr_admin_password" {
  value     = azurerm_container_registry.acr.admin_password
  sensitive = true
}

output "storage_account" {
  value = azurerm_storage_account.docs.name
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}
