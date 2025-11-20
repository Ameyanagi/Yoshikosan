# ==============================================================================
# ヨシコさん、ヨシッ！ - Makefile
# Industrial Safety Management System
# ==============================================================================

# Default target
.DEFAULT_GOAL := help

# ==============================================================================
# Variables
# ==============================================================================
FRONTEND_DIR := yoshikosan-frontend
BACKEND_DIR := yoshikosan-backend
COMPOSE := docker-compose
DOCKER := docker

# ==============================================================================
# Development Commands
# ==============================================================================

.PHONY: dev
dev: ## Start all services in development mode
	@echo "🚀 Starting development environment..."
	$(COMPOSE) up --build

.PHONY: dev-frontend
dev-frontend: ## Start frontend only in development mode
	@echo "🎨 Starting frontend development server..."
	cd $(FRONTEND_DIR) && bun dev

.PHONY: dev-backend
dev-backend: ## Start backend only in development mode
	@echo "⚙️  Starting backend development server..."
	cd $(BACKEND_DIR) && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# ==============================================================================
# Docker Build Commands
# ==============================================================================

.PHONY: docker-build
docker-build: ## Build all Docker images
	@echo "🔨 Building all Docker images..."
	$(COMPOSE) build

.PHONY: docker-build-frontend
docker-build-frontend: ## Build frontend Docker image only
	@echo "🔨 Building frontend Docker image..."
	$(COMPOSE) build frontend

.PHONY: docker-build-backend
docker-build-backend: ## Build backend Docker image only
	@echo "🔨 Building backend Docker image..."
	$(COMPOSE) build backend

# ==============================================================================
# Docker Lifecycle Commands
# ==============================================================================

.PHONY: docker-up
docker-up: ## Start all containers in detached mode
	@echo "▶️  Starting all containers..."
	$(COMPOSE) up -d
	@echo "✅ All services started!"
	@echo "   Frontend: http://localhost:6666/"
	@echo "   Backend API: http://localhost:6666/api/"
	@echo "   API Docs: http://localhost:6666/docs"

.PHONY: docker-down
docker-down: ## Stop and remove all containers
	@echo "⏹️  Stopping all containers..."
	$(COMPOSE) down

.PHONY: docker-logs
docker-logs: ## View logs from all containers (follow mode)
	$(COMPOSE) logs -f

.PHONY: docker-logs-backend
docker-logs-backend: ## View backend logs only
	$(COMPOSE) logs -f backend

.PHONY: docker-logs-frontend
docker-logs-frontend: ## View frontend logs only
	$(COMPOSE) logs -f frontend

.PHONY: docker-restart
docker-restart: docker-down docker-up ## Restart all containers

.PHONY: docker-ps
docker-ps: ## Show running containers and their status
	$(COMPOSE) ps

.PHONY: docker-clean
docker-clean: ## Remove all containers, images, and volumes (DESTRUCTIVE)
	@echo "⚠️  WARNING: This will remove all Docker resources."
	@echo "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	$(COMPOSE) down -v --rmi all
	$(DOCKER) system prune -af --volumes

# ==============================================================================
# Database Commands
# ==============================================================================

.PHONY: db-init
db-init: ## Initialize database with schema migrations
	@echo "🗄️  Initializing database..."
	cd $(BACKEND_DIR) && uv run alembic upgrade head
	@echo "✅ Database initialized!"

.PHONY: db-migrate
db-migrate: ## Generate and apply new database migration
	@echo "🗄️  Generating migration..."
	cd $(BACKEND_DIR) && uv run alembic revision --autogenerate -m "$(shell bash -c 'read -p "Migration message: " msg; echo $$msg')"
	@echo "🗄️  Applying migration..."
	cd $(BACKEND_DIR) && uv run alembic upgrade head
	@echo "✅ Migration complete!"

.PHONY: db-migrate-apply
db-migrate-apply: ## Apply pending migrations (without generating new ones)
	@echo "🗄️  Applying pending migrations..."
	cd $(BACKEND_DIR) && uv run alembic upgrade head
	@echo "✅ Migrations applied!"

.PHONY: db-downgrade
db-downgrade: ## Downgrade database by one migration
	@echo "⏪ Downgrading database..."
	cd $(BACKEND_DIR) && uv run alembic downgrade -1

.PHONY: db-history
db-history: ## Show migration history
	cd $(BACKEND_DIR) && uv run alembic history --verbose

.PHONY: db-current
db-current: ## Show current migration version
	cd $(BACKEND_DIR) && uv run alembic current

.PHONY: db-reset
db-reset: ## Reset database (DESTRUCTIVE - destroys all data)
	@echo "⚠️  WARNING: This will destroy all database data!"
	@echo "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo "⏹️  Stopping database..."
	$(COMPOSE) stop postgres
	$(COMPOSE) rm -f postgres
	@echo "🗑️  Removing database volume..."
	$(DOCKER) volume rm yoshikosan_postgres-data || true
	@echo "▶️  Starting fresh database..."
	$(COMPOSE) up -d postgres
	@echo "⏳ Waiting for database to be ready..."
	sleep 5
	@$(MAKE) db-init
	@echo "✅ Database reset complete!"

.PHONY: db-shell
db-shell: ## Connect to PostgreSQL shell
	@echo "🔌 Connecting to database..."
	$(COMPOSE) exec postgres psql -U yoshikosan -d yoshikosan_db

# ==============================================================================
# Code Quality Commands
# ==============================================================================

.PHONY: lint
lint: lint-frontend lint-backend ## Lint all code (frontend + backend)

.PHONY: lint-frontend
lint-frontend: ## Lint frontend code with ESLint
	@echo "🔍 Linting frontend..."
	cd $(FRONTEND_DIR) && bun run lint

.PHONY: lint-backend
lint-backend: ## Lint backend code with Ruff
	@echo "🔍 Linting backend..."
	cd $(BACKEND_DIR) && uv run ruff check .

.PHONY: format
format: format-frontend format-backend ## Format all code (frontend + backend)

.PHONY: format-frontend
format-frontend: ## Format frontend code with Prettier
	@echo "✨ Formatting frontend..."
	cd $(FRONTEND_DIR) && bun run format

.PHONY: format-backend
format-backend: ## Format backend code with Ruff
	@echo "✨ Formatting backend..."
	cd $(BACKEND_DIR) && uv run ruff format .

.PHONY: typecheck
typecheck: typecheck-frontend typecheck-backend ## Type check all code

.PHONY: typecheck-frontend
typecheck-frontend: ## Type check frontend with TypeScript
	@echo "🔎 Type checking frontend..."
	cd $(FRONTEND_DIR) && bun run typecheck

.PHONY: typecheck-backend
typecheck-backend: ## Type check backend with mypy
	@echo "🔎 Type checking backend..."
	cd $(BACKEND_DIR) && uv run mypy .

.PHONY: test
test: test-backend ## Run all tests

.PHONY: test-backend
test-backend: ## Run backend tests with pytest
	@echo "🧪 Running backend tests..."
	cd $(BACKEND_DIR) && uv run pytest -v

.PHONY: test-backend-cov
test-backend-cov: ## Run backend tests with coverage report
	@echo "🧪 Running backend tests with coverage..."
	cd $(BACKEND_DIR) && uv run pytest --cov=src --cov-report=html --cov-report=term

.PHONY: test-ai-services
test-ai-services: ## Run AI service integration tests (SambaNova + Hume AI)
	@echo "🤖 Running AI service integration tests..."
	cd $(BACKEND_DIR) && uv run pytest tests/ai_services/ -v -s

# ==============================================================================
# Pre-commit Hook Commands
# ==============================================================================

.PHONY: install-hooks
install-hooks: ## Install pre-commit hooks
	@echo "🪝 Installing pre-commit hooks..."
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	@pre-commit install
	@echo "✅ Pre-commit hooks installed!"

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	@echo "🪝 Running pre-commit hooks..."
	pre-commit run --all-files

.PHONY: pre-commit-update
pre-commit-update: ## Update pre-commit hook versions
	pre-commit autoupdate

# ==============================================================================
# Utility Commands
# ==============================================================================

.PHONY: openapi-export
openapi-export: ## Export OpenAPI spec to openapi/openapi.json
	@echo "📄 Exporting OpenAPI specification..."
	@mkdir -p openapi
	@curl -s http://localhost:6666/openapi.json | python3 -m json.tool > openapi/openapi.json
	@echo "✅ OpenAPI spec exported to openapi/openapi.json"

.PHONY: help
help: ## Show this help message
	@echo "ヨシコさん、ヨシッ！- Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Development:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Development Commands" | grep -B 50 "Docker Build" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Docker Build:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Docker Build Commands" | grep -B 50 "Docker Lifecycle" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Docker Lifecycle:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Docker Lifecycle Commands" | grep -B 50 "Database Commands" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Database:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Database Commands" | grep -B 50 "Code Quality" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Code Quality:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Code Quality Commands" | grep -B 50 "Pre-commit Hook" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Pre-commit:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Pre-commit Hook Commands" | grep -B 50 "Utility Commands" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Utilities:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -A 50 "Utility Commands" | grep "^[a-zA-Z]" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""

.PHONY: clean
clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning build artifacts..."
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/.next
	rm -rf $(BACKEND_DIR)/__pycache__ $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete!"

.PHONY: env-check
env-check: ## Validate required environment variables
	@echo "🔍 Checking required environment variables..."
	@test -f .env || (echo "❌ ERROR: .env file not found. Copy .env.example to .env" && exit 1)
	@grep -q "SECRET_KEY=" .env || (echo "❌ ERROR: SECRET_KEY not set" && exit 1)
	@grep -q "DATABASE_URL=" .env || (echo "❌ ERROR: DATABASE_URL not set" && exit 1)
	@grep -q "POSTGRES_PASSWORD=" .env || (echo "❌ ERROR: POSTGRES_PASSWORD not set" && exit 1)
	@grep -q "GOOGLE_CLIENT_ID=" .env || echo "⚠️  WARNING: GOOGLE_CLIENT_ID not set (OAuth won't work)"
	@grep -q "DISCORD_CLIENT_ID=" .env || echo "⚠️  WARNING: DISCORD_CLIENT_ID not set (OAuth won't work)"
	@echo "✅ Required environment variables OK!"

.PHONY: install
install: install-frontend install-backend ## Install all dependencies

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && bun install

.PHONY: install-backend
install-backend: ## Install backend dependencies
	@echo "📦 Installing backend dependencies..."
	cd $(BACKEND_DIR) && uv sync

.PHONY: update
update: update-frontend update-backend ## Update all dependencies

.PHONY: update-frontend
update-frontend: ## Update frontend dependencies
	@echo "⬆️  Updating frontend dependencies..."
	cd $(FRONTEND_DIR) && bun update

.PHONY: update-backend
update-backend: ## Update backend dependencies
	@echo "⬆️  Updating backend dependencies..."
	cd $(BACKEND_DIR) && uv sync --upgrade

.PHONY: check
check: env-check lint typecheck ## Run all checks (env, lint, typecheck)

.PHONY: ci
ci: check test ## Run all CI checks (lint, typecheck, test)

.PHONY: setup
setup: install install-hooks env-check ## Initial project setup (install deps + hooks + check env)
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "   1. Copy .env.example to .env and configure it"
	@echo "   2. Run 'make docker-build' to build images"
	@echo "   3. Run 'make docker-up' to start services"
	@echo "   4. Run 'make db-init' to initialize the database"
	@echo ""
