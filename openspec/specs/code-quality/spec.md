# code-quality Specification

## Purpose
TBD - created by archiving change add-production-deployment. Update Purpose after archive.
## Requirements
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

