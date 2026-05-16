resource "azurerm_search_service" "ai" {
  name                = local.search_name
  resource_group_name = azurerm_resource_group.main.name
  location            = var.search_location
  sku                 = "free"

  # Free tier limita a 1 partition / 1 replica
  partition_count = 1
  replica_count   = 1

  tags = var.tags
}
