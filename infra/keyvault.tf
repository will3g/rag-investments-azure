resource "azurerm_key_vault" "main" {
  name                        = local.kv_name
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  rbac_authorization_enabled  = true
  tags                        = var.tags
}

resource "azurerm_role_assignment" "kv_admin_caller" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Azure RBAC propagation takes ~60s after the role assignment is created
resource "time_sleep" "wait_rbac_propagation" {
  depends_on      = [azurerm_role_assignment.kv_admin_caller]
  create_duration = "120s"
}

resource "azurerm_key_vault_secret" "search_key" {
  name         = "azure-search-key"
  value        = azurerm_search_service.ai.primary_key
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [time_sleep.wait_rbac_propagation]
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "azure-openai-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [time_sleep.wait_rbac_propagation]
}
