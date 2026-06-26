# Load .env (if present) so values like APP_PORT are available to targets.
-include .env
export

APP_PORT ?= 8000

.DEFAULT_GOAL := help
.PHONY: help init qdrant-up qdrant-down qdrant-restart index run

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

init: ## Install dependencies (uv sync) and create .env from .env.example
	uv sync
	@test -f .env || cp .env.example .env
	@echo "Setup complete. Edit .env to add your OPENAI_API_KEY."

qdrant-up: ## Start the Qdrant container
	docker compose up -d

qdrant-down: ## Stop and remove the Qdrant container
	docker compose down

qdrant-restart: ## Restart the Qdrant container
	docker compose restart

index: ## Ingest whatever XML is in data/rag into Qdrant
	uv run python -m rag.ingest

run: ## Start the Chainlit app
	uv run chainlit run frontend/app.py --port $(APP_PORT)
