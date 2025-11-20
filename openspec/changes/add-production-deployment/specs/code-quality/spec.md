# Spec: Code Quality Enforcement

**Capability:** code-quality
**Status:** Draft
**Last Updated:** 2025-11-21

## Overview

Provide automated code quality enforcement through pre-commit hooks for both frontend and backend, ensuring consistent code style, type safety, and linting standards.

## ADDED Requirements

### Requirement: Pre-commit Hook Configuration

The system SHALL provide pre-commit hook configuration for automated code quality checks.

**Rationale:** Prevent low-quality code from being committed by enforcing checks before each commit.

#### Scenario: Pre-commit framework setup

**Given** the project uses Git for version control
**When** pre-commit hooks are configured
**Then** `.pre-commit-config.yaml` SHALL exist in the project root
**And** the configuration SHALL define hooks for both frontend and backend
**And** hooks SHALL run automatically before each git commit
**And** commits SHALL be blocked if hooks fail

#### Scenario: Hook installation

**Given** a developer clones the repository
**When** running `make install-hooks` or `pre-commit install`
**Then** Git hooks SHALL be installed in `.git/hooks/`
**And** the pre-commit framework SHALL be installed
**And** hook dependencies SHALL be downloaded and cached
**And** the installation SHALL complete without errors

#### Scenario: Manual hook execution

**Given** pre-commit hooks are installed
**When** running `make lint` or `pre-commit run --all-files`
**Then** all hooks SHALL run on all files
**And** results SHALL be displayed with clear pass/fail status
**And** failed files SHALL be listed with specific errors
**And** the command SHALL exit with non-zero code on failure

---

### Requirement: Backend Code Quality Checks

The system SHALL enforce Python code quality using Ruff and mypy.

**Rationale:** Ensure backend code follows PEP 8 standards, type safety, and modern Python best practices.

#### Scenario: Ruff linting

**Given** Python files are committed
**When** pre-commit hooks run
**Then** Ruff SHALL check all Python files for linting issues
**And** Ruff SHALL use project configuration from `pyproject.toml`
**And** violations SHALL be reported with line numbers
**And** the commit SHALL be blocked if linting fails

#### Scenario: Ruff formatting

**Given** Python files are committed
**When** pre-commit hooks run
**Then** Ruff SHALL auto-format all Python files
**And** formatting SHALL be consistent with Black style
**And** line length SHALL be enforced (default 88 characters)
**And** formatted files SHALL be staged automatically

#### Scenario: mypy type checking

**Given** Python files have type annotations
**When** pre-commit hooks run
**Then** mypy SHALL verify type correctness
**And** mypy SHALL use strict mode for type checking
**And** type errors SHALL be reported with file and line numbers
**And** the commit SHALL be blocked if type errors exist

#### Scenario: Python version compatibility

**Given** the backend requires Python 3.13
**When** configuring quality checks
**Then** tools SHALL target Python 3.13 syntax
**And** deprecated features SHALL be flagged
**And** type stubs SHALL be compatible with Python 3.13

---

### Requirement: Frontend Code Quality Checks

The system SHALL enforce TypeScript/JavaScript code quality using ESLint and Prettier.

**Rationale:** Ensure frontend code follows consistent style, React best practices, and type safety.

#### Scenario: ESLint checking

**Given** TypeScript/JavaScript files are committed
**When** pre-commit hooks run
**Then** ESLint SHALL check all TypeScript and JavaScript files
**And** ESLint SHALL use Next.js recommended config
**And** React hooks rules SHALL be enforced
**And** the commit SHALL be blocked if linting fails

#### Scenario: Prettier formatting

**Given** TypeScript/JavaScript files are committed
**When** pre-commit hooks run
**Then** Prettier SHALL auto-format all files
**And** formatting SHALL be consistent across the codebase
**And** formatted files SHALL be staged automatically
**And** configuration SHALL match project style guide

#### Scenario: TypeScript type checking

**Given** TypeScript files are committed
**When** running `make typecheck`
**Then** TypeScript compiler SHALL verify type correctness
**And** strict mode SHALL be enabled
**And** type errors SHALL be reported with file and line numbers
**And** the build SHALL fail if type errors exist

#### Scenario: File scope

**Given** the frontend contains multiple file types
**When** hooks run
**Then** hooks SHALL apply to `.ts`, `.tsx`, `.js`, `.jsx` files
**And** hooks SHALL apply to configuration files (`.json`, `.yaml`)
**And** hooks SHALL exclude `node_modules` and `.next`
**And** hooks SHALL exclude generated files

---

### Requirement: Configuration Files

The system SHALL provide configuration files for all quality tools.

**Rationale:** Centralize and version-control tool configurations for consistency.

#### Scenario: Ruff configuration

**Given** Ruff needs project-specific rules
**When** configuring in `pyproject.toml`
**Then** line length SHALL be set to 88 characters
**And** target Python version SHALL be 3.13
**And** select rules SHALL include: E (pycodestyle), F (pyflakes), I (isort), N (pep8-naming)
**And** ignore rules SHALL be documented

#### Scenario: mypy configuration

**Given** mypy needs strict type checking
**When** configuring in `pyproject.toml`
**Then** strict mode SHALL be enabled
**And** disallow_untyped_defs SHALL be true
**And** warn_return_any SHALL be true
**And** Python version SHALL be 3.13

#### Scenario: ESLint configuration

**Given** ESLint needs Next.js and React rules
**When** configuring in `.eslintrc.json`
**Then** extends SHALL include `next/core-web-vitals`
**And** React hooks plugin SHALL be enabled
**And** TypeScript parser SHALL be configured
**And** custom rules SHALL be documented

#### Scenario: Prettier configuration

**Given** Prettier needs consistent formatting
**When** configuring in `.prettierrc`
**Then** semi-colons SHALL be enforced
**And** single quotes SHALL be used
**And** trailing commas SHALL be set to `es5`
**And** print width SHALL be 100 characters

---

### Requirement: Makefile Integration

The system SHALL integrate quality checks into Makefile commands.

**Rationale:** Provide convenient commands for developers to run quality checks manually.

#### Scenario: Install hooks command

**Given** pre-commit hooks need installation
**When** running `make install-hooks`
**Then** pre-commit framework SHALL be installed
**And** Git hooks SHALL be configured
**And** hook dependencies SHALL be cached
**And** success message SHALL be displayed

#### Scenario: Lint command

**Given** code needs linting
**When** running `make lint`
**Then** backend linting (Ruff) SHALL run
**And** frontend linting (ESLint) SHALL run
**And** all errors SHALL be displayed together
**And** the command SHALL exit with non-zero on failure

#### Scenario: Format command

**Given** code needs formatting
**When** running `make format`
**Then** backend formatting (Ruff) SHALL run
**And** frontend formatting (Prettier) SHALL run
**And** files SHALL be formatted in-place
**And** the command SHALL report formatted files

#### Scenario: Typecheck command

**Given** code needs type checking
**When** running `make typecheck`
**Then** backend type checking (mypy) SHALL run
**And** frontend type checking (tsc) SHALL run
**And** all type errors SHALL be displayed
**And** the command SHALL exit with non-zero on failure

---

### Requirement: CI/CD Integration

The system SHALL support quality checks in CI/CD pipelines.

**Rationale:** Ensure code quality is verified before merging to main branch.

#### Scenario: Pre-commit in CI

**Given** CI/CD pipeline runs on pull requests
**When** the pipeline executes
**Then** pre-commit hooks SHALL run on all files
**And** the pipeline SHALL fail if hooks fail
**And** results SHALL be visible in the CI output

#### Scenario: Separate check stages

**Given** CI/CD pipeline needs granular feedback
**When** defining pipeline stages
**Then** linting SHALL be a separate stage
**And** type checking SHALL be a separate stage
**And** formatting SHALL be a separate stage
**And** each stage failure SHALL be clearly reported

## Implementation Notes

### .pre-commit-config.yaml

```yaml
# Pre-commit hooks configuration
repos:
  # Backend: Ruff for linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      # Run linter
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        files: ^yoshikosan-backend/
      # Run formatter
      - id: ruff-format
        files: ^yoshikosan-backend/

  # Backend: mypy for type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        files: ^yoshikosan-backend/
        args: [--strict, --python-version=3.13]
        additional_dependencies:
          - types-all

  # Frontend: ESLint
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.17.0
    hooks:
      - id: eslint
        files: ^yoshikosan-frontend/
        types: [file]
        types_or: [javascript, jsx, ts, tsx]
        args: [--fix, --max-warnings=0]
        additional_dependencies:
          - eslint@9.17.0
          - eslint-config-next@16.0.0
          - typescript@5.7.2

  # Frontend: Prettier
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        files: ^yoshikosan-frontend/
        types_or: [javascript, jsx, ts, tsx, json, yaml, markdown]
        args: [--write]

  # General: trailing whitespace and end of file
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
```

### pyproject.toml (Backend Configuration)

```toml
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = [
    "E501", # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
follow_imports = "normal"
```

### .eslintrc.json (Frontend Configuration)

```json
{
  "extends": ["next/core-web-vitals", "next/typescript"],
  "rules": {
    "react/no-unescaped-entities": "off",
    "@typescript-eslint/no-unused-vars": [
      "error",
      {
        "argsIgnorePattern": "^_",
        "varsIgnorePattern": "^_"
      }
    ],
    "@typescript-eslint/no-explicit-any": "error"
  }
}
```

### .prettierrc (Frontend Configuration)

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### .prettierignore

```
# Dependencies
node_modules

# Build output
.next
out
dist
build

# Cache
.turbo
.eslintcache

# Env files
.env*

# Database
postgres-data
```

### Makefile Integration

```makefile
.PHONY: install-hooks
install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	@pre-commit install
	@echo "✓ Pre-commit hooks installed"

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
	@echo "Type checking frontend..."
	cd $(FRONTEND_DIR) && bun run typecheck
	@echo "Type checking backend..."
	cd $(BACKEND_DIR) && uv run mypy .

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files
```

### Frontend package.json Scripts

```json
{
  "scripts": {
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "format:check": "prettier --check \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "typecheck": "tsc --noEmit"
  }
}
```

## Testing Requirements

1. **Hook Installation:** `make install-hooks` SHALL complete successfully
2. **Backend Linting:** Ruff SHALL catch common Python issues
3. **Backend Type Checking:** mypy SHALL catch type errors
4. **Frontend Linting:** ESLint SHALL catch React/Next.js issues
5. **Frontend Formatting:** Prettier SHALL format consistently
6. **Commit Blocking:** Commits with quality issues SHALL be blocked
7. **Manual Execution:** `make lint`, `make format`, `make typecheck` SHALL work

## Dependencies

- pre-commit framework
- Ruff 0.8.4+ (backend linting/formatting)
- mypy 1.13+ (backend type checking)
- ESLint 9.17+ (frontend linting)
- Prettier 4.0+ (frontend formatting)
- Node.js/Bun (for frontend tools)
- Python 3.13 (for backend tools)

## Related Specs

- `automation` - Makefile commands for running quality checks
- `containerization` - Quality checks in Docker build process
