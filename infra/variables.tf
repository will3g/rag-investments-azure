variable "prefix" {
  description = "Prefixo para os nomes dos recursos (3-10 caracteres minúsculos)"
  type        = string
  default     = "ragmba"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,9}$", var.prefix))
    error_message = "prefix deve começar com letra e ter 3-10 caracteres minúsculos/dígitos."
  }
}

variable "location" {
  description = "Região Azure padrão para a maioria dos recursos"
  type        = string
  default     = "brazilsouth"
}

variable "openai_location" {
  description = "Região para o recurso de Azure OpenAI (nem toda região suporta os modelos)"
  type        = string
  default     = "eastus"
}

variable "search_location" {
  description = "Região para o Azure AI Search (Free tier suportado em poucas regiões)"
  type        = string
  default     = "eastus"
}

variable "container_image" {
  description = "Imagem do container a ser deployada (ACR loginserver/repo:tag)"
  type        = string
  default     = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
}

variable "openai_embedding_model" {
  description = "Modelo de embeddings a ser provisionado no Azure OpenAI"
  type        = string
  default     = "text-embedding-3-small"
}

variable "openai_chat_model" {
  description = "Modelo de chat a ser provisionado no Azure OpenAI"
  type        = string
  default     = "gpt-4o"
}

variable "tags" {
  description = "Tags aplicadas em todos os recursos"
  type        = map(string)
  default = {
    project     = "rag-investimentos"
    environment = "dev"
    course      = "fiap-mba"
  }
}
