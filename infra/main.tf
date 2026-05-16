resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
  numeric = true
}

locals {
  suffix          = random_string.suffix.result
  base_name       = "${var.prefix}${local.suffix}"
  rg_name         = "rg-${local.base_name}"
  storage_name    = "st${local.base_name}" # Storage account: 3-24 chars, sem hífen
  search_name     = "srch-${local.base_name}"
  openai_name     = "oai-${local.base_name}"
  acr_name        = "acr${local.base_name}" # ACR: alfanumérico, 5-50
  cae_name        = "cae-${local.base_name}"
  ca_name         = "ca-${local.base_name}-api"
  kv_name         = "kv-${local.base_name}"
  log_name        = "log-${local.base_name}"
  container_image = var.container_image
}

resource "azurerm_resource_group" "main" {
  name     = local.rg_name
  location = var.location
  tags     = var.tags
}

data "azurerm_client_config" "current" {}
