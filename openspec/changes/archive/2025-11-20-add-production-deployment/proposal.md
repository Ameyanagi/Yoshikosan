# Proposal: Add Production-Ready Deployment Infrastructure

**Change ID:** `add-production-deployment`
**Status:** Draft
**Created:** 2025-11-21
**Author:** AI Assistant

## Problem Statement

The project currently lacks production-ready deployment infrastructure:
- ❌ No Dockerfiles for frontend or backend (references exist in docker-compose.yml but files don't exist)
- ❌ No Makefile for task automation
- ❌ Authentication (Google OAuth, Discord OAuth) not implemented in backend
- ❌ Database connectivity not configured
- ❌ No production build optimization

Currently, `docker-compose.yml` and `nginx.conf` exist but reference non-existent Dockerfiles, making the system non-functional.

## Proposed Solution

Create a complete production deployment infrastructure accessible at https://yoshikosan.ameyanagi.com:

### 1. **Containerization** (`specs/containerization/`)
- Production-optimized Dockerfile for Next.js frontend (multi-stage build with Bun)
- Production-optimized Dockerfile for FastAPI backend (multi-stage build with uv)
- Properly configured docker-compose.yml with all services

### 2. **Task Automation** (`specs/automation/`)
- Comprehensive Makefile with commands for:
  - Development workflow (dev, build, test)
  - Docker operations (docker-build, docker-up, docker-down)
  - Database management (db-init, db-migrate, db-reset)
  - Code quality (lint, format, typecheck)

### 3. **Deployment Configuration** (`specs/deployment-config/`)
- Environment variable management
- Database initialization scripts
- Health checks and readiness probes
- Logging configuration

### 4. **Authentication Implementation** (`specs/authentication/`)
- Email/password authentication (registration, login)
- OAuth backend implementation (Google, Discord)
- JWT token generation and validation
- User database schema and models
- Minimal authentication UI (login/register forms, OAuth buttons)

### 5. **Code Quality Enforcement** (`specs/code-quality/`)
- Pre-commit hooks for automated checks
- Backend: Ruff (linting/formatting) + mypy (type checking)
- Frontend: ESLint + Prettier
- Git hook configuration

## Scope

### In Scope
✅ Production Dockerfiles (frontend & backend)
✅ Docker Compose orchestration
✅ Makefile automation
✅ Environment configuration templates
✅ Database connectivity setup
✅ **Email/password authentication (registration, login)**
✅ **OAuth implementation (Google, Discord) - backend code**
✅ **Minimal authentication UI (login/register forms, OAuth buttons)**
✅ **Database schema for users, OAuth accounts, and sessions**
✅ **Pre-commit hooks (Ruff, mypy, ESLint, Prettier)**

### Out of Scope
❌ Full user profile management UI
❌ Password reset/forgot password functionality
❌ Email verification
❌ Advanced authorization (roles, permissions)
❌ CI/CD pipeline
❌ SSL/TLS certificate management (handled externally)
❌ Social profile data synchronization
❌ Two-factor authentication (2FA)

## Success Criteria

1. ✅ `docker-compose up` successfully builds and starts all services
2. ✅ Frontend accessible at http://localhost:6666/
3. ✅ Backend API accessible at http://localhost:6666/api/
4. ✅ Backend OpenAPI docs accessible at http://localhost:6666/docs
5. ✅ Database connection established and healthy
6. ✅ All environment variables properly loaded
7. ✅ `make` commands work for common tasks
8. ✅ Production builds are optimized (frontend < 300MB, backend < 250MB)
9. ✅ **Email/password registration and login work correctly**
10. ✅ **OAuth flows work for Google and Discord**
11. ✅ **Pre-commit hooks enforce code quality**
12. ✅ **Database migrations apply successfully**

## Dependencies

- Existing: `docker-compose.yml`, `nginx.conf`, `.env.example`
- Required: Docker, Docker Compose, Make, Bun 1.3, uv (Python 3.13)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Large Docker image sizes | Slow deployments | Multi-stage builds, layer optimization |
| Missing environment variables | Runtime failures | Comprehensive .env.example with validation |
| Build failures | Deployment blocked | Clear error messages, build validation |
| Database connection issues | Service unavailable | Health checks, retry logic |

## Timeline Estimate

- Dockerfiles & Docker Compose: 3-4 hours
- Makefile automation: 2-3 hours
- Database schema & migrations: 3-4 hours
- Authentication backend (email/password + OAuth): 6-8 hours
- Authentication frontend UI: 3-4 hours
- Code quality setup (pre-commit hooks): 2-3 hours
- Testing & validation: 3-4 hours
- Documentation: 2-3 hours

**Total: 24-33 hours**

## Related Documents

- `openspec/project.md` - Project context and tech stack
- `.env.example` - Environment variables
- `docker-compose.yml` - Service orchestration (needs Dockerfiles)
- `nginx.conf` - Reverse proxy configuration
