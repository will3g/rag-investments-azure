# Azure: RAG para Investimentos

**Repositório**: https://github.com/will3g/rag-investments-azure

Aplicação RAG (Retrieval-Augmented Generation) end-to-end sobre documentos de
**investimentos brasileiros** (Tesouro Direto, renda fixa, renda variável,
FIIs, tributação e glossário).

> Cobre os 5 critérios da rubrica + bônus de IaC (Terraform Azure).

## Stack

| Camada           | Tecnologia                                    |
|------------------|-----------------------------------------------|
| API              | FastAPI + Uvicorn                             |
| Chunking         | LangChain `RecursiveCharacterTextSplitter`    |
| Embeddings       | Azure OpenAI (`text-embedding-3-small`)       |
| Vector store     | Azure AI Search (Free tier)                   |
| LLM              | Azure OpenAI `gpt-4o`                    |
| Container        | Docker multi-stage (Python 3.12-slim)         |
| Hospedagem       | Azure Container Apps (scale-to-zero)          |
| Registry         | Azure Container Registry                      |
| Secrets          | Azure Key Vault                               |
| IaC              | Terraform (provider `azurerm`)                |
| Testes           | pytest + httpx + mocks                        |

## Estrutura

```
.
├── app/                 # código da aplicação
│   ├── api/             # rotas + schemas Pydantic
│   ├── core/            # config + logging
│   └── rag/             # chunker, embeddings, retriever, generator, pipeline
├── data/investimentos/  # 6 documentos curados em Markdown
├── docker/              # Dockerfile multi-stage
├── docs/                # ARCHITECTURE.md + DEPLOY.md
├── infra/               # Terraform Azure (bônus IaC)
├── scripts/ingest.py    # CLI de ingestão
└── tests/               # pytest com mocks de Azure OpenAI / AI Search
```

## Deploy em Azure

Passo a passo para publicar a API em produção.

### Pré-requisitos

- Conta Azure com permissão para criar recursos.
- **Azure OpenAI habilitado** na subscription (preencher o formulário em
  https://aka.ms/oai/access). Sem isso o `terraform apply` falhará na criação
  do `azurerm_cognitive_account`.
- CLIs instaladas localmente:
  ```bash
  az version       # >= 2.60
  terraform -v     # >= 1.6
  docker --version # >= 24
  ```

### 1. Login na Azure

```bash
az login
az account show          # confira a subscription correta
az account set --subscription "<subscription-id>"
```

### 2. Provisionar a infraestrutura

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
make tf-init
make tf-plan
make tf-apply
```

Recursos criados (~5–10 min):

- Resource Group `rg-ragmba<sufixo>`
- Storage Account + container `raw-docs`
- Azure AI Search (Free tier)
- Azure OpenAI + 2 deployments (embedding + chat)
- Container Registry (ACR)
- Container App Environment + Container App (com placeholder image)
- Key Vault + secrets
- Log Analytics Workspace

Capture os outputs:

```bash
terraform output
terraform output -raw acr_login_server
terraform output -raw acr_admin_username
terraform output -raw acr_admin_password
terraform output -raw api_url
```

### 3. Build e push da imagem

```bash
make docker-push
```

### 4. Atualizar o Container App com a imagem real

Edite `infra/terraform.tfvars`:

```hcl
container_image = "<acr-server>/rag-investimentos:latest"
```

E aplique:

```bash
make tf-plan
make tf-apply
```

### 5. Ingerir os documentos

```bash
# pegue as credenciais geradas pelo Terraform
export AZURE_SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
export AZURE_SEARCH_KEY=$(terraform output -raw search_admin_key)
export AZURE_SEARCH_INDEX=investimentos
export AZURE_OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint)
export AZURE_OPENAI_API_KEY=$(terraform output -raw openai_api_key)
export AZURE_OPENAI_API_VERSION=2024-08-01-preview
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
export AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
export LLM_PROVIDER=azure

cp .env.example .env

make install
make ingest
```

### 6. Testar a API

```bash
API_URL=$(cd infra && terraform output -raw api_url)

curl -s "$API_URL/health" | jq

curl -s -X POST "$API_URL/query" \
  -H 'Content-Type: application/json' \
  -d '{"question": "O que é Tesouro Selic?"}' | jq
```

### Destruir tudo (após a entrega)

```bash
make tf-destroy
```

## Endpoints

| Método | Path     | Descrição                                       |
|--------|----------|-------------------------------------------------|
| GET    | /health  | Liveness + provider configurado                 |
| POST   | /ingest  | Indexa um documento (`{text, source}`)          |
| POST   | /query   | Faz uma consulta RAG (`{question, top_k?}`)     |
| GET    | /docs    | Swagger UI                                      |

### Exemplos de uso

**1. Tributação de FIIs**

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "Qual a tributação dos FIIs?"}'
```

```json
{
  "answer": "Os rendimentos pagos a pessoa física são isentos de IR... [#1]",
  "sources": [
    {
      "chunk": "FIIs são obrigados por lei a distribuir pelo menos 95% do lucro...",
      "source": "fiis.md",
      "score": 0.91,
      "position": 2,
      "ingested_at": "2025-05-16T12:00:00+00:00"
    }
  ]
}
```

**2. Tesouro Selic**

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "O que é Tesouro Selic e para quem é indicado?"}'
```

```json
{
  "answer": "O Tesouro Selic (LFT) é um título pós-fixado que acompanha a taxa Selic... [#1][#2]",
  "sources": [
    {
      "chunk": "O Tesouro Selic tem liquidez diária e é considerado o investimento mais seguro...",
      "source": "tesouro_direto.md",
      "score": 0.94,
      "position": 1,
      "ingested_at": "2025-05-16T12:00:00+00:00"
    }
  ]
}
```

**3. Indexadores de renda fixa**

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "Quais são os principais indexadores de renda fixa no Brasil?"}'
```

```json
{
  "answer": "Os principais indexadores são: CDI (Certificado de Depósito Interbancário), IPCA (inflação oficial) e Selic... [#1]",
  "sources": [
    {
      "chunk": "CDI é a taxa de referência para investimentos pós-fixados em renda fixa...",
      "source": "renda_fixa.md",
      "score": 0.89,
      "position": 0,
      "ingested_at": "2025-05-16T12:00:00+00:00"
    }
  ]
}
```
