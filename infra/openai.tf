resource "azurerm_cognitive_account" "openai" {
  name                  = local.openai_name
  location              = var.openai_location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = local.openai_name
  tags                  = var.tags
}

resource "azurerm_cognitive_deployment" "embedding" {
  name                 = var.openai_embedding_model
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format = "OpenAI"
    name   = var.openai_embedding_model
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = var.openai_chat_model
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.openai_chat_model
    version = "2024-11-20"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 30
  }
}
