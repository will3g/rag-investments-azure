.PHONY: help install dev run test lint clean ingest docker-build docker-run docker-push \
        tf-init tf-plan tf-apply tf-destroy tf-output

PYTHON ?= python3.12
VENV   ?= .venv
ACTIVATE = . $(VENV)/bin/activate

help: ## Mostra este help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Cria venv e instala dependências (prod + dev)
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip && pip install -e ".[dev]"

dev: ## Roda API local em modo reload
	$(ACTIVATE) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run: ## Roda API local sem reload (modo prod)
	$(ACTIVATE) && uvicorn app.main:app --host 0.0.0.0 --port 8000

ingest: ## Indexa todos os documentos em data/ no Azure AI Search
	$(ACTIVATE) && python -m scripts.ingest

test: ## Roda pytest
	$(ACTIVATE) && pytest

lint: ## Roda ruff
	$(ACTIVATE) && ruff check . && ruff format --check .

format: ## Formata com ruff
	$(ACTIVATE) && ruff format . && ruff check --fix .

clean: ## Remove venv e caches
	rm -rf $(VENV) .pytest_cache .ruff_cache **/__pycache__ *.egg-info

# ----- Docker -----------------------------------------------------------------
docker-build: ## Build imagem Docker
	docker build -f docker/Dockerfile -t rag-investimentos:latest .

docker-run: ## Roda container Docker (passa .env)
	docker run --rm -p 8000:8000 --env-file .env rag-investimentos:latest

docker-push: ## Build linux/amd64, login no ACR e push
	$(eval ACR_SERVER := $(shell cd infra && terraform output -raw acr_login_server))
	$(eval ACR_USER   := $(shell cd infra && terraform output -raw acr_admin_username))
	$(eval ACR_PASS   := $(shell cd infra && terraform output -raw acr_admin_password))
	echo "$(ACR_PASS)" | docker login "$(ACR_SERVER)" -u "$(ACR_USER)" --password-stdin
	docker buildx build --platform linux/amd64 -f docker/Dockerfile \
		-t "$(ACR_SERVER)/rag-investimentos:latest" --push .

# ----- Terraform --------------------------------------------------------------
tf-init: ## terraform init
	cd infra && terraform init
	cp infra/terraform.tfvars.example infra/terraform.tfvars

tf-plan: ## terraform plan
	cd infra && terraform plan -out=tfplan

tf-apply: ## terraform apply
	cd infra && terraform apply tfplan

tf-destroy: ## terraform destroy (DESTRUTIVO — pede confirmação)
	cd infra && terraform destroy

tf-output: ## Mostra outputs (URLs, endpoints)
	cd infra && terraform output
