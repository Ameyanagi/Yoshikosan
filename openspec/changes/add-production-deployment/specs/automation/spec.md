# Spec: Task Automation

**Capability:** automation
**Status:** Draft
**Last Updated:** 2025-11-21

## Overview

Provide a comprehensive Makefile for automating common development, build, deployment, and maintenance tasks.

## ADDED Requirements

### Requirement: Development Workflow Commands

The system SHALL provide Make commands for local development workflows.

**Rationale:** Simplify local development by providing consistent, easy-to-remember commands.

#### Scenario: Start all services in development mode

**Given** the developer wants to run the entire stack locally
**When** running `make dev`
**Then** the frontend SHALL start in development mode on port 3000
**And** the backend SHALL start in development mode on port 8000
**And** PostgreSQL SHALL start in a Docker container
**And** all services SHALL auto-reload on file changes

#### Scenario: Start frontend only

**Given** the developer wants to work on frontend only
**When** running `make dev-frontend`
**Then** only the frontend SHALL start in development mode
**And** the frontend SHALL use Bun dev server
**And** hot module replacement SHALL be enabled

#### Scenario: Start backend only

**Given** the developer wants to work on backend only
**When** running `make dev-backend`
**Then** only the backend SHALL start in development mode
**And** the backend SHALL use uvicorn with --reload
**And** the virtual environment SHALL be activated

---

### Requirement: Docker Build Commands

The system SHALL provide Make commands for building and managing Docker containers.

**Rationale:** Standardize Docker operations across the team with simple commands.

#### Scenario: Build all Docker images

**Given** Dockerfiles exist for frontend and backend
**When** running `make docker-build`
**Then** both frontend and backend images SHALL be built
**And** the build process SHALL use caching
**And** build errors SHALL be clearly displayed

#### Scenario: Build frontend image only

**Given** the frontend Dockerfile has changed
**When** running `make docker-build-frontend`
**Then** only the frontend image SHALL be rebuilt
**And** the backend image SHALL remain unchanged
**And** the build SHALL complete in < 5 minutes

#### Scenario: Build backend image only

**Given** the backend Dockerfile has changed
**When** running `make docker-build-backend`
**Then** only the backend image SHALL be rebuilt
**And** the frontend image SHALL remain unchanged
**And** the build SHALL complete in < 5 minutes

---

### Requirement: Docker Lifecycle Commands

The system SHALL provide Make commands for managing running containers.

**Rationale:** Simplify Docker Compose operations with memorable commands.

#### Scenario: Start all containers

**Given** Docker images have been built
**When** running `make docker-up`
**Then** all services SHALL start in detached mode
**And** services SHALL start in dependency order
**And** the command SHALL exit after services are running

#### Scenario: Stop all containers

**Given** containers are currently running
**When** running `make docker-down`
**Then** all containers SHALL be stopped and removed
**And** networks SHALL be removed
**And** volumes SHALL be preserved

#### Scenario: View container logs

**Given** containers are running
**When** running `make docker-logs`
**Then** logs from all services SHALL be displayed
**And** logs SHALL follow in real-time
**And** logs SHALL be color-coded by service

#### Scenario: Restart all containers

**Given** containers are running
**When** running `make docker-restart`
**Then** all containers SHALL be stopped
**And** all containers SHALL be started again
**And** the operation SHALL preserve data volumes

#### Scenario: Clean Docker resources

**Given** Docker resources exist from previous runs
**When** running `make docker-clean`
**Then** all containers SHALL be stopped and removed
**And** all images SHALL be removed
**And** all volumes SHALL be removed
**And** the user SHALL be prompted for confirmation

---

### Requirement: Database Management Commands

The system SHALL provide Make commands for database operations.

**Rationale:** Simplify database management tasks for developers.

#### Scenario: Initialize database

**Given** the database is empty or doesn't exist
**When** running `make db-init`
**Then** the database SHALL be created
**And** initial schema SHALL be applied
**And** seed data SHALL be loaded (if available)

#### Scenario: Run database migrations

**Given** new migrations exist
**When** running `make db-migrate`
**Then** Alembic SHALL generate or run migrations
**And** the database schema SHALL be updated
**And** migration history SHALL be tracked

#### Scenario: Reset database

**Given** the developer wants a clean database
**When** running `make db-reset`
**Then** all tables SHALL be dropped
**And** the schema SHALL be recreated
**And** seed data SHALL be reloaded
**And** the user SHALL be prompted for confirmation

#### Scenario: Connect to database shell

**Given** the database container is running
**When** running `make db-shell`
**Then** a psql shell SHALL open
**And** the user SHALL be connected to the yoshikosan database
**And** SQL commands can be executed interactively

---

### Requirement: Code Quality Commands

The system SHALL provide Make commands for code quality checks.

**Rationale:** Ensure consistent code quality across frontend and backend.

#### Scenario: Lint all code

**Given** code exists in both frontend and backend
**When** running `make lint`
**Then** ESLint SHALL run on frontend code
**And** Ruff SHALL run on backend code
**And** all linting errors SHALL be displayed

#### Scenario: Format all code

**Given** code exists in both frontend and backend
**When** running `make format`
**Then** Prettier SHALL format frontend code
**And** Ruff SHALL format backend code
**And** all files SHALL be formatted in-place

#### Scenario: Type check all code

**Given** code has type annotations
**When** running `make typecheck`
**Then** TypeScript compiler SHALL check frontend code
**And** mypy SHALL check backend code
**And** type errors SHALL be clearly displayed

#### Scenario: Run all tests

**Given** tests exist for frontend and backend
**When** running `make test`
**Then** Bun test SHALL run frontend tests
**And** pytest SHALL run backend tests
**And** test results SHALL be displayed with coverage

---

### Requirement: Utility Commands

The system SHALL provide utility commands for common tasks.

**Rationale:** Provide helpful commands for setup, cleanup, and information.

#### Scenario: Display help information

**Given** a developer is new to the project
**When** running `make help` or just `make`
**Then** all available commands SHALL be listed
**And** each command SHALL have a brief description
**And** commands SHALL be grouped by category

#### Scenario: Clean build artifacts

**Given** build artifacts exist from previous builds
**When** running `make clean`
**Then** node_modules SHALL be removed from frontend
**And** .next build output SHALL be removed
**And** __pycache__ SHALL be removed from backend
**And** .pytest_cache SHALL be removed

#### Scenario: Validate environment variables

**Given** a .env file exists
**When** running `make env-check`
**Then** all required variables SHALL be validated
**And** missing variables SHALL be listed
**And** invalid values SHALL be flagged

---

### Requirement: Makefile Best Practices

The Makefile SHALL follow best practices for maintainability and usability.

**Rationale:** Ensure the Makefile is easy to understand, modify, and extend.

#### Scenario: Phony targets

**Given** Make targets don't create files
**When** defining targets in the Makefile
**Then** all targets SHALL be marked as .PHONY
**And** target names SHALL not conflict with file names

#### Scenario: Command documentation

**Given** each Make target serves a purpose
**When** viewing the Makefile
**Then** each target SHALL have a comment describing its purpose
**And** the help command SHALL extract these descriptions
**And** documentation SHALL be consistent

#### Scenario: Error handling

**Given** commands may fail
**When** a command in a target fails
**Then** the Make process SHALL stop immediately
**And** the error message SHALL be displayed clearly
**And** partial changes SHALL be visible for debugging

#### Scenario: Variable defaults

**Given** some settings may vary by environment
**When** defining variables in the Makefile
**Then** sensible defaults SHALL be provided
**And** variables SHALL be overridable via environment
**And** critical variables SHALL be documented

## Implementation Notes

### Makefile Structure
```makefile
# Default target
.DEFAULT_GOAL := help

# Variables
FRONTEND_DIR := yoshikosan-frontend
BACKEND_DIR := yoshikosan-backend
COMPOSE := docker-compose
DOCKER := docker

# Development Commands
.PHONY: dev
dev: ## Start all services in development mode
	@echo "Starting development environment..."
	$(COMPOSE) up --build

.PHONY: dev-frontend
dev-frontend: ## Start frontend only in development mode
	@echo "Starting frontend..."
	cd $(FRONTEND_DIR) && bun dev

.PHONY: dev-backend
dev-backend: ## Start backend only in development mode
	@echo "Starting backend..."
	cd $(BACKEND_DIR) && uv run uvicorn src.main:app --reload

# Docker Commands
.PHONY: docker-build
docker-build: ## Build all Docker images
	$(COMPOSE) build

.PHONY: docker-up
docker-up: ## Start all containers in background
	$(COMPOSE) up -d

.PHONY: docker-down
docker-down: ## Stop and remove all containers
	$(COMPOSE) down

.PHONY: docker-logs
docker-logs: ## View logs from all containers
	$(COMPOSE) logs -f

.PHONY: docker-restart
docker-restart: docker-down docker-up ## Restart all containers

.PHONY: docker-clean
docker-clean: ## Remove all containers, images, and volumes
	@echo "This will remove all Docker resources. Continue? [y/N]"
	@read ans && [ $${ans:-N} = y ]
	$(COMPOSE) down -v
	$(DOCKER) system prune -af

# Database Commands
.PHONY: db-init
db-init: ## Initialize database with schema
	cd $(BACKEND_DIR) && uv run alembic upgrade head

.PHONY: db-migrate
db-migrate: ## Create or run database migrations
	cd $(BACKEND_DIR) && uv run alembic revision --autogenerate
	cd $(BACKEND_DIR) && uv run alembic upgrade head

.PHONY: db-reset
db-reset: ## Reset database (WARNING: destroys data)
	@echo "This will destroy all data. Continue? [y/N]"
	@read ans && [ $${ans:-N} = y ]
	$(COMPOSE) down -v postgres
	$(COMPOSE) up -d postgres
	sleep 5
	$(MAKE) db-init

.PHONY: db-shell
db-shell: ## Connect to PostgreSQL shell
	$(COMPOSE) exec postgres psql -U yoshikosan -d yoshikosan_db

# Quality Commands
.PHONY: lint
lint: lint-frontend lint-backend ## Lint all code

.PHONY: lint-frontend
lint-frontend: ## Lint frontend code
	cd $(FRONTEND_DIR) && bun run lint

.PHONY: lint-backend
lint-backend: ## Lint backend code
	cd $(BACKEND_DIR) && uv run ruff check .

.PHONY: format
format: format-frontend format-backend ## Format all code

.PHONY: format-frontend
format-frontend: ## Format frontend code
	cd $(FRONTEND_DIR) && bun run format

.PHONY: format-backend
format-backend: ## Format backend code
	cd $(BACKEND_DIR) && uv run ruff format .

.PHONY: typecheck
typecheck: ## Type check all code
	cd $(FRONTEND_DIR) && bun run typecheck
	cd $(BACKEND_DIR) && uv run mypy .

.PHONY: test
test: test-backend ## Run all tests

.PHONY: test-backend
test-backend: ## Run backend tests
	cd $(BACKEND_DIR) && uv run pytest

# Utility Commands
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: ## Clean build artifacts and caches
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/.next
	rm -rf $(BACKEND_DIR)/__pycache__ $(BACKEND_DIR)/.pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: env-check
env-check: ## Validate environment variables
	@echo "Checking required environment variables..."
	@test -f .env || (echo "ERROR: .env file not found" && exit 1)
	@grep -q "SECRET_KEY=" .env || (echo "ERROR: SECRET_KEY not set" && exit 1)
	@grep -q "DATABASE_URL=" .env || (echo "ERROR: DATABASE_URL not set" && exit 1)
	@echo "✓ Environment variables OK"
```

## Testing Requirements

1. **Command Execution:** All Make commands SHALL execute without syntax errors
2. **Help Output:** `make help` SHALL display all commands with descriptions
3. **Error Handling:** Failed commands SHALL exit with non-zero status
4. **Idempotency:** Running commands multiple times SHALL be safe

## Dependencies

- GNU Make 4.0+
- Docker & Docker Compose
- Bun 1.3+ (for frontend commands)
- uv (for backend commands)

## Related Specs

- `containerization` - Docker images that Makefile commands build/run
- `deployment-config` - Environment variables validated by env-check
