# Project Context

## Current Project Status

**✅ Already Set Up:**
- Next.js 16 frontend with TypeScript 5 (`yoshikosan-frontend/`)
- Tailwind CSS v4 with new PostCSS plugin
- Bun 1.3 package manager and tooling
- ESLint 9 configuration
- shadcn/ui component library
- Python 3.13 backend with uv (`yoshikosan-backend/`)
- Basic project structure (OpenSpec, git repos)
- Docker infrastructure (docker-compose.yml, nginx.conf)

**🔨 To Be Implemented:**
- FastAPI backend structure (DDD layers)
- Database setup (PostgreSQL + SQLAlchemy + Alembic)
- Authentication system (JWT + OAuth)
- AI service integrations (SambaNova, Hume AI)
- Frontend UI components (shadcn/ui)
- State management (React Query, Zustand)
- Testing infrastructure (pytest, Bun test)
- Docker containerization
- Makefile for task automation

## Purpose
**ヨシコさん、ヨシッ！(Yoshiko-san, Yoshi!)** - 現場の「よし！」を、最強の安全装置に変える

A next-generation industrial safety management system that digitizes Japan's "指差呼称" (pointing and calling) safety practice. The system uses multimodal AI to verify that workers follow Standard Operating Procedures (SOPs) in real-time, preventing incidents before they occur.

### Core Goals
1. **Prevent workplace accidents** by enforcing proper safety confirmation procedures
2. **Digitize traditional safety practices** ("Yoshi!" verbal confirmations) with AI-powered verification
3. **Provide real-time feedback** to workers during procedures using voice and vision AI
4. **Automate safety logging** to eliminate manual reporting burden
5. **Make safety visible** to management through data-driven insights

### Key Value Proposition
According to Heinrich's Law (1:29:300), behind every serious accident lie 29 minor accidents and 300 near-misses. ヨシコさん、ヨシッ！ targets the elimination of these 300 near-misses by:
- Transforming passive "pointing and calling" into an active AI trigger
- Providing instant feedback when procedures are skipped or incorrect
- Creating an automated safety audit trail

## Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5
- **UI Library**: React 19
- **Styling**: Tailwind CSS v4 (with @tailwindcss/postcss)
- **Package Manager**: Bun 1.3 (fast, all-in-one JavaScript toolkit)
  - Package manager, bundler, runtime, test runner in one
  - 30x faster than npm
  - Native TypeScript and JSX support
- **Component Library**: shadcn/ui (already added)
- **State Management**: React Query (TanStack Query) for server state, Zustand for client state (to be added)
- **Forms**: React Hook Form + Zod validation (to be added)
- **API Client**: Native Fetch API with TypeScript types

### Backend
- **Framework**: FastAPI (Python 3.13)
- **Language**: Python 3.13 (fixed version) with type hints (required)
- **Package Manager**: uv (extremely fast, modern Python package manager)
  - Replaces pip, poetry, virtualenv, and more
  - Written in Rust, 10-100x faster than pip
  - Built-in Python version management
- **API**: RESTful API with automatic OpenAPI/Swagger documentation
- **Architecture**: Domain-Driven Design (DDD) principles
- **Database ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL (production), SQLite (development/testing)
- **Authentication**: FastAPI Security + JWT tokens
  - OAuth2 with password flow (username/password)
  - Google OAuth integration
  - Discord OAuth integration
- **Validation**: Pydantic v2 for request/response models
- **Async**: AsyncIO for all I/O operations (database, HTTP, file operations)

### AI/ML Integration
- **LLM**: SambaNova (fast inference for multimodal analysis)
  - Vision + text analysis for SOP verification
  - Support for various open-source models (Llama, Qwen, etc.)
- **Speech-to-Text**: Browser Web Speech API or local Whisper
- **Text-to-Speech**: Hume AI (empathic voice synthesis)
  - Emotionally intelligent voice feedback
  - Appropriate tone for safety contexts (calm guidance vs. urgent warnings)
  - Natural-sounding Japanese language support
- **Voice Activity Detection**: On-device or lightweight keyword spotting for "Yoshi!" trigger

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Deployment**: https://yoshikosan.ameyanagi.com (HTTPS)
  - External proxy redirects to http://host.docker.internal:6666
  - SSL/TLS termination handled outside Docker
- **Reverse Proxy**: Nginx (required for path-based routing)
  - Port 6666 → Nginx (inside Docker)
  - `/` → Frontend (Next.js on internal port 3000)
  - `/api/*` → Backend (FastAPI on internal port 8000)
- **Environment Variables**: `.env` for secrets and configuration

### Development Tools
- **Python Package Manager**: uv (primary) - Python version and dependency management
- **Frontend Package Manager**: Bun 1.3 (includes runtime, bundler, test runner, package manager)
- **Testing (Backend)**: pytest + pytest-asyncio + httpx
- **Testing (Frontend)**: Bun's built-in test runner (Jest-compatible, extremely fast)
- **Linting (Backend)**: Ruff (extremely fast Python linter/formatter)
- **Linting (Frontend)**: ESLint 9 (flat config)
- **Formatting (Backend)**: Ruff (replaces black + isort)
- **Formatting (Frontend)**: Prettier (or Biome for speed)
- **Type Checking (Backend)**: mypy or Pyright
- **Type Checking (Frontend)**: TypeScript 5 strict mode

## Project Conventions

### Code Style

#### Backend (Python/FastAPI)
- **Language**: Python 3.13 (fixed version) with type hints (required)
- **Package Manager**: uv for all dependency management
  - Install: `uv venv` to create virtual environment
  - Install deps: `uv pip install -r requirements.txt` or `uv sync`
  - Add packages: `uv add <package>`
  - Run scripts: `uv run <command>`
- **Naming Conventions**:
  - Files: snake_case (`user_profile.py`, `api_client.py`)
  - Classes: PascalCase (`UserProfile`, `SafetyCheckService`)
  - Functions/Variables: snake_case (`get_user_data`, `is_check_complete`)
  - Constants: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `API_BASE_URL`)
  - Private members: prefix with underscore (`_internal_method`)
- **Formatting**: Ruff (replaces black + isort, much faster)
  - Line length: 88 characters
  - Automatic import sorting
- **Imports**: Absolute imports preferred, grouped (stdlib → third-party → local)
- **Type Hints**: Required for all function signatures and class attributes
- **Docstrings**: Google-style docstrings for all public functions/classes
- **Async**: Prefer `async def` for all I/O operations (database, HTTP, file I/O)

#### Frontend (TypeScript/Next.js)
- **Language**: TypeScript with strict mode enabled
- **Naming Conventions**:
  - Files: kebab-case (`user-profile.tsx`, `api-client.ts`)
  - Components: PascalCase (`UserProfile.tsx`, `SafetyCheckButton.tsx`)
  - Functions/Variables: camelCase (`getUserData`, `isCheckComplete`)
  - Constants: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `API_BASE_URL`)
  - Types/Interfaces: PascalCase with descriptive names (`UserProfile`, `SafetyCheckResult`)
- **Formatting**: Prettier with default settings
- **Imports**: Absolute imports using `@/` prefix (maps to root directory, e.g., `@/components`, `@/lib`)
- **Component Structure**: Use functional components with hooks
- **Props**: Define explicit TypeScript interfaces for all component props
- **Styling**: Tailwind CSS v4
  - Uses new `@tailwindcss/postcss` plugin (not `tailwindcss/postcss`)
  - Import in CSS: `@import "tailwindcss";` (not `@tailwind base/components/utilities`)
  - Config: `tailwind.config.ts` (TypeScript-based)
  - No need for `content` config in v4 (auto-detected)

### Architecture Patterns

#### Monorepo Structure
```
/
├── yoshikosan-backend/      # FastAPI backend
│   ├── src/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── api/            # API routes and endpoints
│   │   │   ├── v1/        # API version 1
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── sop.py
│   │   │   │   │   ├── safety_check.py
│   │   │   │   │   └── auth.py
│   │   │   │   └── api.py  # Router aggregation
│   │   │   └── deps.py     # Dependency injection
│   │   ├── domain/         # Domain layer (DDD)
│   │   │   ├── sop/       # SOP aggregate
│   │   │   │   ├── entities.py
│   │   │   │   ├── value_objects.py
│   │   │   │   ├── repositories.py  # Interfaces (Protocols)
│   │   │   │   └── services.py      # Domain services
│   │   │   ├── safety_check/
│   │   │   └── user/
│   │   ├── application/    # Application layer (use cases)
│   │   │   ├── sop/
│   │   │   │   ├── structure_sop.py
│   │   │   │   └── validate_sop.py
│   │   │   └── safety_check/
│   │   │       └── verify_check.py
│   │   ├── infrastructure/ # Infrastructure layer
│   │   │   ├── database/
│   │   │   │   ├── models.py         # SQLAlchemy models
│   │   │   │   ├── repositories/     # Concrete implementations
│   │   │   │   │   └── sop_repository.py
│   │   │   │   └── session.py        # Async DB session management
│   │   │   ├── ai_services/
│   │   │   │   ├── sambanova.py      # SambaNova LLM client
│   │   │   │   └── hume.py           # Hume AI TTS client
│   │   │   └── storage/              # File storage
│   │   ├── core/           # Core/shared code
│   │   │   ├── config.py   # Settings (Pydantic BaseSettings)
│   │   │   ├── security.py # Auth utilities (JWT, OAuth)
│   │   │   └── exceptions.py
│   │   └── schemas/        # Pydantic schemas (API models)
│   │       ├── sop.py
│   │       ├── safety_check.py
│   │       └── user.py
│   ├── tests/
│   │   ├── unit/          # Unit tests (domain, services)
│   │   ├── integration/   # Integration tests (repos, APIs)
│   │   └── conftest.py    # Pytest fixtures
│   ├── alembic/           # Database migrations
│   ├── pyproject.toml     # uv project config
│   ├── .python-version    # Python version (3.13)
│   └── Dockerfile
├── yoshikosan-frontend/     # Next.js frontend
│   ├── app/               # Next.js App Router (root level, not src/)
│   │   ├── (auth)/       # Route group: Auth-protected routes
│   │   ├── (public)/     # Route group: Public routes
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── globals.css   # Global styles
│   ├── components/        # React components (to be created)
│   │   ├── ui/           # shadcn/ui components
│   │   └── features/     # Feature-specific components
│   ├── lib/              # Utility functions (to be created)
│   │   ├── api-client.ts # FastAPI client
│   │   └── utils.ts      # General utilities
│   ├── hooks/            # Custom React hooks (to be created)
│   ├── types/            # TypeScript type definitions (to be created)
│   ├── public/           # Static assets
│   ├── package.json
│   ├── bun.lock          # Bun lockfile
│   ├── tsconfig.json     # TypeScript config
│   ├── next.config.ts    # Next.js config
│   ├── tailwind.config.ts # Tailwind CSS config
│   ├── postcss.config.mjs # PostCSS config (Tailwind v4)
│   └── Dockerfile
├── openspec/             # OpenSpec change proposals
│   ├── AGENTS.md        # Agent instructions
│   ├── project.md       # This file
│   └── proposals/       # Change proposals
├── docker-compose.yml   # Multi-service orchestration
├── Makefile            # Task automation
├── .env                # Environment variables (gitignored)
├── .gitignore
└── README.md
```

**Key Structure Notes:**
- **Frontend uses `app/` directory at root level** (not `src/app/`), following Next.js 13+ App Router conventions
- **TypeScript path alias `@/*`** maps to `./*` (root), so `@/components` = `./components`
- **Backend uses `src/` directory** for Python source code
- **Monorepo**: Single git repository for all services
- **Bun 1.3 for frontend**: Fast all-in-one toolkit (package manager, bundler, runtime, test runner)
- **uv for backend**: Ultra-fast Python package and project manager (10-100x faster than pip)

#### Domain-Driven Design (DDD) Structure (Backend)

The backend follows DDD principles with clear layer separation:

**Domain Layer** (`src/domain/`)
- **Entities**: Core business objects with identity (e.g., `SOP`, `SafetyCheck`, `User`)
  - Rich domain models with business logic
  - Dataclasses or Pydantic models with methods
  - Example: `SOP` entity with methods like `add_step()`, `validate()`
- **Value Objects**: Immutable objects without identity (e.g., `StepNumber`, `DangerLevel`)
  - Compare by value, not reference
  - Encapsulate validation logic
  - Example: `DangerLevel` with validation ensuring 1-5 range
- **Repositories**: Abstract base classes (protocols) for data access
  - Example: `SOPRepository` protocol (interface)
  - Implementation in infrastructure layer
- **Domain Services**: Business logic that doesn't fit in entities
  - Example: `SOPStructuringService` for AI-powered SOP parsing

**Application Layer** (`src/application/`)
- **Use Cases**: Orchestrate domain objects to fulfill requests
  - Example: `StructureSOPUseCase`, `VerifySafetyCheckUseCase`
  - Coordinate repositories, domain services, and external services
  - Transaction boundaries
  - Async functions for I/O operations
- Keep thin - delegate to domain layer

**Infrastructure Layer** (`src/infrastructure/`)
- **Concrete Implementations**: Database, external APIs, file systems
  - Example: `SQLAlchemySOPRepository` implements `SOPRepository` protocol
  - SambaNova service adapters for multimodal LLM operations
  - Hume AI service adapters for empathic TTS
- **Adapters**: Convert between domain models and database/API formats
- **SQLAlchemy Models**: Separate from domain entities (avoid tight coupling)

**Presentation Layer** (`src/api/`)
- **FastAPI Routers**: Expose use cases as HTTP endpoints
  - Thin layer - call application services
  - Handle input validation (Pydantic schemas)
  - Map domain exceptions to HTTP errors
  - Dependency injection for services and database sessions

**Key DDD Principles**:
- **Ubiquitous Language**: Use domain terms (SOP, 指差呼称, KY) in code
- **Bounded Contexts**: Separate contexts for SOP management, Safety Checks, User management
- **Aggregates**: SOP is an aggregate root containing Steps and Danger Points
- **Repository Pattern**: Abstract data access behind protocols/interfaces
- **Domain Events**: Emit events for important occurrences (e.g., `SafetyCheckFailed`)
- **Separation of Concerns**: UI → API → Application → Domain → Infrastructure

#### Key Patterns
- **API Communication**: REST API with OpenAPI spec (auto-generated by FastAPI)
- **Data Fetching**: React Query for server state management (frontend)
- **Authentication**: JWT tokens with FastAPI Security, HTTP-only cookies
- **Error Handling**:
  - Backend: Custom exceptions mapped to HTTP status codes
  - Frontend: Error boundaries and toast notifications
- **AI Integration**:
  - Structured prompts stored as constants/templates
  - Multimodal input handling (audio + image + structured SOP data)
  - Response parsing with Pydantic schemas for type safety

#### SOP (Standard Operating Procedure) Flow
1. **Upload Phase**: User uploads SOP document (image/PDF/text) via frontend
2. **Structuring Phase**: Backend LLM parses into structured JSON with steps and danger points
3. **Verification Phase**: User reviews and corrects AI interpretation
4. **Execution Phase**: Real-time monitoring with "Yoshi!" voice triggers
5. **Logging Phase**: Automatic recording of compliance data

### Testing Strategy

#### Backend Testing (pytest)
- **Unit Testing**: Test domain entities, value objects, and services in isolation
  - Example: `test_sop_entity.py` - test SOP validation, step addition logic
  - Example: `test_danger_level_vo.py` - test value object validation
  - Pure business logic, no dependencies, very fast
  - Use pytest with type checking enabled
- **Integration Testing**: Test API endpoints with test database
  - Example: `test_sop_endpoints.py` with httpx async client
  - Use pytest fixtures for database setup/teardown
  - Test database: SQLite in-memory or PostgreSQL test instance
- **Repository Tests**: Test repository implementations with test database
  - Example: `test_sop_repository.py` with async SQLAlchemy
- **Use Case Tests**: Test application services with mocked repositories
  - Mock infrastructure dependencies
  - Verify orchestration logic

#### Frontend Testing
**Not required for MVP** - Focus on backend unit tests for safety-critical logic.

If testing becomes needed later:
- E2E tests with Playwright for critical user flows
- Manual testing for UI/UX validation

**Testing Guidelines**
- **Coverage Target**: >80% for backend domain and application layers (safety-critical)
- **Test Structure**: Arrange-Act-Assert pattern
- **Mocking**: Use dependency injection for testability
  - Repositories are protocols, easily mocked
  - AI services behind adapters, mocked in tests
- **Fast Feedback**: Unit tests should run in <2 seconds
- **CI/CD**: Run backend tests on pull requests before merge
- **Async Testing**: Use pytest-asyncio for async tests
- **Focus**: Backend unit tests only (domain entities, value objects, services, repositories)

### Build & Task Automation

**Makefile Structure**
- All common tasks are automated via `Makefile`
- Commands are organized into logical groups:
  - Development: `dev`, `dev-frontend`, `dev-backend`, `build`
  - Testing: `test`, `test-backend`, `test-frontend`, `test-coverage`
  - Database: `db-*` commands for Alembic migrations
  - Docker: `docker-*` commands for container management
  - Quality: `lint`, `format`, `typecheck`, `check`
  - Utilities: `clean`, `help`
- Run `make help` to see all available commands
- Use `make` for consistency across development and CI/CD

**Why Make?**
- **Consistency**: Same commands work locally and in CI
- **Simplicity**: No need to remember complex Python/npm/Docker commands
- **Documentation**: Makefile serves as executable documentation
- **Composability**: Complex workflows built from simple targets
- **Cross-platform**: Works on Linux, macOS, and Windows (with WSL/Git Bash)

### Git Workflow
- **Branching Strategy**: GitHub Flow
  - `main`: Production-ready code
  - `feature/*`: New features
  - `fix/*`: Bug fixes
  - `chore/*`: Maintenance tasks
- **Commit Conventions**: Conventional Commits
  - `feat:` New features
  - `fix:` Bug fixes
  - `docs:` Documentation changes
  - `chore:` Tooling/config changes
  - `refactor:` Code refactoring
  - `test:` Test additions/changes
- **PR Process**: Require code review before merging to main

## Domain Context

### Manufacturing Safety Terminology
- **指差呼称 (Shisa Kosho / Pointing and Calling)**: Japanese safety practice where workers point at equipment and verbally confirm status ("Valve closed, Yoshi!")
- **SOP (Standard Operating Procedure)**: Step-by-step instructions for completing tasks safely
- **KY (危険予知 / Kiken Yochi / Hazard Prediction)**: Risk assessment document identifying potential dangers
- **Heinrich's Law (1:29:300)**: For every major accident, there are 29 minor accidents and 300 near-misses
- **Yoshi (よし!)**: "Good!" or "Check!" - the verbal confirmation used in pointing and calling

### User Personas
1. **Field Workers**: Perform procedures, need hands-free guidance and safety net
2. **Safety Managers**: Monitor compliance, analyze incident patterns, generate reports
3. **New Employees**: Learning procedures, need step-by-step guidance
4. **Veteran Workers**: May skip steps due to overconfidence, need gentle reminders

### Safety Requirements
- **Real-time feedback**: Must provide immediate correction if procedure is incorrect
- **Offline capability**: Should work in areas with poor connectivity (cache SOPs locally)
- **Non-intrusive**: Must not interfere with actual work (hands-free, voice-driven)
- **Audit trail**: Every "Yoshi!" check must be logged with timestamp, user, image, and result
- **Privacy**: Worker monitoring must comply with labor laws, no unnecessary recording

## Important Constraints

### Technical Constraints
- **Deployment**: https://yoshikosan.ameyanagi.com
  - HTTPS terminated by external proxy
  - Proxied to http://host.docker.internal:6666
  - Nginx handles internal routing within Docker
- **Routing**: Path-based routing
  - `/` → Frontend (internal port 3000)
  - `/api/*` → Backend (internal port 8000, rewritten to remove `/api` prefix)
- **Mobile Support**: UI must work on smartphones (workers use phones in the field)
- **Hands-free Operation**: Core functionality should work without touching the device
- **Response Time**: AI feedback must be < 3 seconds for good UX
- **API Communication**: Frontend calls backend via `/api/*` (proxied by Nginx)
- **CORS**: Nginx handles internal routing, CORS config needed for HTTPS domain

### Business Constraints
- **Hackathon MVP Scope**:
  - SOP upload and structuring (image → JSON via SambaNova LLM)
  - Manual "Yoshi!" button (voice trigger nice-to-have)
  - Single-image capture and AI verification
  - TTS feedback with OK/NG + next step guidance (Hume AI)
  - Basic logging (no advanced analytics yet)
- **Budget**: Use SambaNova and Hume AI APIs efficiently (optimize prompt tokens, cache when possible)

### Regulatory Constraints
- **Data Privacy**: Worker activity logs may contain personal data (GDPR/privacy law compliance)
- **Safety Liability**: System is assistive, not replacement for human judgment
- **Audit Requirements**: Logs must be immutable and traceable for incident investigations

## External Dependencies

### APIs and Services
- **SambaNova API**:
  - Fast inference for multimodal analysis (vision + text)
  - Open-source model support (Llama, Qwen, etc.)
  - SOP structuring and safety verification
- **Hume AI API**:
  - Empathic text-to-speech for voice feedback
  - Emotionally appropriate safety guidance
  - Japanese language support
- **OAuth Providers**:
  - Google OAuth (needs client ID/secret)
  - Discord OAuth (needs client ID/secret)

### Environment Variables Required
```bash
# Deployment
DOMAIN="yoshikosan.ameyanagi.com"
EXTERNAL_PORT="6666"  # Docker port (accessed via host.docker.internal)

# Database (Docker service name: postgres)
DATABASE_URL="postgresql://yoshikosan:your_password@postgres:5432/yoshikosan_db"

# Backend API (internal, not exposed externally)
API_HOST="0.0.0.0"
API_PORT="8000"  # Internal port within Docker network
SECRET_KEY="your-secret-key-here-change-in-production"  # For JWT signing
ALLOWED_ORIGINS="https://yoshikosan.ameyanagi.com"  # HTTPS without port

# OAuth Providers
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
DISCORD_CLIENT_ID="your-discord-client-id"
DISCORD_CLIENT_SECRET="your-discord-client-secret"
OAUTH_REDIRECT_URI="https://yoshikosan.ameyanagi.com/auth/callback"  # HTTPS

# AI Services
SAMBANOVA_API_KEY="your-sambanova-api-key"      # SambaNova API for LLM
HUME_AI_API_KEY="your-hume-ai-api-key"          # Hume AI for empathic TTS

# Frontend (internal, not exposed externally)
NEXT_PUBLIC_API_URL="/api"  # Relative path (proxied by Nginx)
PORT="3000"  # Internal port within Docker network

# Application
NODE_ENV="production"
```

**Environment Variable Notes:**
- **HTTPS setup**: External proxy handles HTTPS → HTTP (host.docker.internal:6666)
- **ALLOWED_ORIGINS**: Use HTTPS domain without port (SSL terminated externally)
- **OAuth redirect**: Use HTTPS URLs (external-facing URL)
- Frontend calls backend via `/api` (relative path), Nginx proxies to `http://backend:8000`
- Database host is `postgres` (Docker service name), not `localhost`
- Docker exposes port 6666 to host, accessed via host.docker.internal
- For development, use separate `.env.development` with `localhost` URLs

### Infrastructure Dependencies
- **Make**: Task automation (Makefile-based commands)
- **Python 3.13**: Backend runtime (fixed version, managed by uv)
- **uv**: Python package manager and environment manager
- **Bun 1.3**: Frontend runtime and package manager
- **Docker**: Required for containerization
- **Docker Compose**: For orchestrating services (nginx + frontend + backend + postgres)
- **Nginx**: Reverse proxy for path-based routing (required)
- **PostgreSQL**: Primary database

## Development Setup Notes

### Initial Setup

#### Prerequisites Installation
```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Bun (JavaScript runtime and package manager)
curl -fsSL https://bun.sh/install | bash

# Verify installations
uv --version  # Should show uv version
bun --version # Should show bun 1.3.x
```

#### Project Setup
```bash
# Clone and navigate to project
cd /home/ryuichi/dev/yoshikosan

# Set up environment variables (root level)
cp .env.example .env
# Edit .env with your secrets

# Install backend dependencies with uv
cd yoshikosan-backend
uv venv                    # Create virtual environment
uv pip install fastapi sqlalchemy alembic pytest httpx ruff mypy
# Or if using pyproject.toml: uv sync
cd ..

# Install frontend dependencies with Bun
cd yoshikosan-frontend
bun install
cd ..

# Initialize database
make db-init

# Run development servers
make dev  # Starts both frontend and backend
```

### Common Make Commands
```bash
# Development
make dev              # Start both frontend and backend dev servers
make dev-frontend     # Start frontend only
make dev-backend      # Start backend only
make build            # Build both frontend and backend for production
make test             # Run all tests (frontend + backend)
make test-backend     # Run backend tests only
make test-frontend    # Run frontend tests only
make test-coverage    # Run tests with coverage report

# Database
make db-init          # Initialize database (run migrations)
make db-migrate       # Create new migration
make db-upgrade       # Run pending migrations
make db-downgrade     # Rollback last migration
make db-reset         # Reset database (drop + migrate)

# Docker
make docker-build     # Build Docker images
make docker-up        # Start containers in background
make docker-down      # Stop and remove containers
make docker-logs      # View container logs
make docker-restart   # Restart containers

# Code Quality
make lint             # Run linters (both backend and frontend)
make lint-backend     # Lint Python code (Ruff)
make lint-frontend    # Lint TypeScript code (ESLint 9)
make format           # Format code (Ruff + Prettier)
make format-backend   # Format Python code (Ruff)
make format-frontend  # Format TypeScript code (Prettier)
make typecheck        # Run type checkers (mypy/pyright + tsc)
make check            # Run lint + typecheck + test

# Utilities
make clean            # Clean build artifacts and cache
make help             # Show all available commands
```

### Docker Deployment
```bash
# Build and start containers
make docker-up

# View logs
make docker-logs

# Stop containers
make docker-down

# Full rebuild
make docker-build && make docker-up
```

### Production Deployment Architecture

The application uses **path-based routing** with Nginx inside Docker:

```
Client (Browser)
     ↓
https://yoshikosan.ameyanagi.com
     ↓
External Proxy (HTTPS → HTTP)
     ↓
http://host.docker.internal:6666
     ↓
Docker: Nginx (port 6666)
     ↓
     ├─ / → Frontend (Next.js on port 3000)
     │       http://frontend:3000
     │
     └─ /api/* → Backend (FastAPI on port 8000)
             http://backend:8000
             (URL rewritten: /api/users → /users)
```

**Key Points:**
- **HTTPS termination**: External proxy handles SSL/TLS
- **Docker access**: http://host.docker.internal:6666 (from external proxy)
- **Path-based routing**: Nginx inspects request path inside Docker
- **URL rewriting**: `/api/users` becomes `/users` when proxied to backend
- **Internal network**: Frontend, backend, database communicate via Docker network
- **CORS configuration**: Backend must allow https://yoshikosan.ameyanagi.com

## AI Assistant Guidelines

When working on this project:

1. **Safety First**: Any changes to safety-critical logic (AI verification, SOP parsing) require extra scrutiny

2. **Type Safety**:
   - Backend: Always use type hints, never use `Any` without justification
   - Frontend: Always use TypeScript types, never use `any`

3. **Use Make Commands**: Always prefer `make` commands over direct Python/Bun/Docker commands
   - Example: Use `make test` instead of `pytest` or `bun test`
   - Example: Use `make dev-frontend` instead of `cd yoshikosan-frontend && bun dev`
   - Example: Use `make docker-up` instead of `docker-compose up -d`
   - Run `make help` to see all available commands

3a. **Use Bun 1.3 for Frontend**: The frontend uses Bun, not npm/yarn/pnpm
   - Install: `bun install` (not `npm install`)
   - Run: `bun dev` (not `npm run dev`)
   - Test: `bun test` (built-in test runner, extremely fast)
   - Note: Path alias `@/*` maps to `./*` (root), not `./src/*`

3b. **Use uv for Backend**: The backend uses uv, not pip/poetry/pipenv
   - Create venv: `uv venv` (not `python -m venv`)
   - Install: `uv pip install <package>` or `uv add <package>`
   - Sync deps: `uv sync` (reads pyproject.toml)
   - Run commands: `uv run <command>`
   - Python version: Managed by uv (3.13 fixed)

4. **Follow DDD Principles**: Respect layer boundaries (Domain → Application → Infrastructure)
   - Keep domain logic pure (no database/API dependencies)
   - Use repository protocols, implement in infrastructure layer
   - Business logic belongs in entities/domain services, not FastAPI routers

5. **Write Tests**: Always write tests for new domain logic
   - Test entities and value objects in isolation
   - Mock repositories in application layer tests
   - Use pytest for backend, Bun's test runner for frontend

5a. **Use Modern Tools**:
   - Backend: Use uv for package management (10-100x faster than pip) and Ruff for linting/formatting
   - Frontend: Use Bun 1.3 for all operations (package management, dev server, testing - 30x faster than npm)

6. **User Context**: Remember workers may be wearing gloves, in noisy environments, or unable to look at screen

7. **Japanese Language**: UI should support Japanese (workers' primary language)

8. **Prompt Engineering**: SOP verification prompts are critical - changes should be tested thoroughly

9. **Logging**: All safety checks must be logged (timestamp, user, step, result, image)

10. **Error Handling**: Never fail silently - workers need to know if verification failed

11. **API Design**:
    - Use RESTful conventions
    - Return proper HTTP status codes
    - Include detailed error messages in responses
    - Use Pydantic for request/response validation

12. **Async/Await**: Use async functions for I/O operations (database, API calls)

## Future Roadmap (Post-MVP)
- Voice trigger with "Yoshi!" keyword detection
- Wearable camera support (chest-mounted for better POV)
- Advanced analytics dashboard for safety managers
- Multi-company/multi-site support
- Offline-first architecture with sync
- Gamification (badges for consistent safe behavior)
- Integration with existing ERP/MES systems
- Mobile apps (native iOS/Android) for better performance
