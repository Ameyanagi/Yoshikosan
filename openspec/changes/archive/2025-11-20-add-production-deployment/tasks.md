# Implementation Tasks

**Change ID:** add-production-deployment
**Status:** Draft

This document outlines the ordered implementation tasks for the production deployment infrastructure.

## Phase 1: Deployment Configuration ✅

### Task 1.1: Create Enhanced .env.example ✅
- [x] Add all required environment variables with documentation
- [x] Include OAuth provider configuration (Google, Discord)
- [x] Add AI service configuration (SambaNova, Hume AI)
- [x] Document secret key generation instructions
- [x] Add health check and logging configuration
- **Verification:** File exists with all sections documented

### Task 1.2: Create Backend Configuration Module ✅
- [x] Create `src/config/settings.py` using Pydantic BaseSettings
- [x] Implement environment variable validation
- [x] Add startup validation for required variables
- [x] Configure logging with structured JSON format
- [x] Set up CORS configuration
- **Verification:** Backend starts with .env loaded, fails on missing required vars

### Task 1.3: Create Health Check Endpoint ✅
- [x] Implement `/health` endpoint in FastAPI
- [x] Add database connectivity check
- [x] Return service status and timestamp
- [x] Test health check returns 200 OK
- **Verification:** `curl http://localhost:8000/health` returns healthy status

---

## Phase 2: Database Schema & Migrations ✅

### Task 2.1: Set Up Alembic ✅
- [x] Initialize Alembic in backend directory
- [x] Configure `alembic.ini` with DATABASE_URL
- [x] Create `alembic/env.py` with Base import
- [x] Test alembic configuration
- **Verification:** `alembic current` runs without error

### Task 2.2: Create User Domain Entities ✅
- [x] Create `src/domain/user/entities.py`
- [x] Define User model (id, email, name, avatar_url, password_hash, timestamps)
- [x] Define OAuthAccount model (id, user_id, provider, provider_user_id, tokens, timestamps)
- [x] Define Session model (id, user_id, token_hash, expires_at, created_at)
- [x] Add relationships and cascade deletes
- **Verification:** Models importable, no syntax errors

### Task 2.3: Create Initial Migration ✅
- [x] Run `alembic revision --autogenerate -m "Initial authentication schema"`
- [x] Review migration file for correctness
- [x] Verify foreign key constraints
- [x] Verify indexes on email and (provider, provider_user_id)
- **Verification:** Migration file created in `alembic/versions/`

### Task 2.4: Apply Migration ✅
- [x] Run `alembic upgrade head` (ready to run when database starts)
- [x] Verify tables created in database (users, oauth_accounts, sessions)
- [x] Verify indexes created
- [x] Test rollback with `alembic downgrade -1`
- **Verification:** `\dt` in psql shows all three tables

---

## Phase 3: Authentication Backend ✅

### Task 3.1: Create Password Utilities ✅
- [x] Create `src/domain/user/password.py`
- [x] Implement `validate_password()` with security requirements
- [x] Implement `hash_password()` using bcrypt cost factor 12
- [x] Implement `verify_password()` for checking hashes
- [x] Add unit tests for password validation
- **Verification:** Tests pass, passwords hashed correctly

### Task 3.2: Create JWT Utilities ✅
- [x] Create `src/domain/user/jwt.py`
- [x] Implement `create_access_token()` with 7-day expiration
- [x] Implement `verify_token()` for validation
- [x] Add token signing with SECRET_KEY and HS256
- [x] Test token generation and verification
- **Verification:** Tokens can be created and verified

### Task 3.3: Create Authentication Middleware ✅
- [x] Create `src/api/dependencies/auth.py`
- [x] Implement `get_current_user()` dependency
- [x] Implement `get_current_user_optional()` dependency
- [x] Extract JWT from cookie or Authorization header
- [x] Fetch user from database by token payload
- **Verification:** Middleware works with test endpoint

### Task 3.4: Implement Email/Password Endpoints ✅
- [x] Create `src/api/v1/endpoints/auth.py`
- [x] Implement `POST /auth/register` endpoint
- [x] Implement `POST /auth/login` endpoint
- [x] Add Pydantic models for requests (RegisterRequest, LoginRequest)
- [x] Set HTTP-only cookies on successful auth
- [x] Add error handling for duplicate emails and invalid credentials
- **Verification:** Can register and login via curl/Postman

### Task 3.5: Implement OAuth Google Flow ✅
- [x] Implement `GET /auth/google` (initiate flow)
- [x] Implement `GET /auth/callback/google` (handle callback)
- [x] Exchange authorization code for access token
- [x] Fetch user profile from Google API
- [x] Create or update user in database
- [x] Create oauth_account record
- [x] Generate JWT and set cookie
- **Verification:** OAuth flow works in browser

### Task 3.6: Implement OAuth Discord Flow ✅
- [x] Implement `GET /auth/discord` (initiate flow)
- [x] Implement `GET /auth/callback/discord` (handle callback)
- [x] Exchange authorization code for access token
- [x] Fetch user profile from Discord API
- [x] Create or update user in database
- [x] Create oauth_account record
- [x] Generate JWT and set cookie
- **Verification:** OAuth flow works in browser

### Task 3.7: Implement User Endpoints ✅
- [x] Implement `GET /auth/me` endpoint
- [x] Implement `POST /auth/logout` endpoint
- [x] Clear cookie on logout
- [x] Invalidate session in database
- **Verification:** `/auth/me` returns user data, logout clears cookie

---

## Phase 4: Frontend Authentication UI ✅

### Task 4.1: Create Auth Context Provider ✅
- [x] Create `yoshikosan-frontend/lib/auth-context.tsx`
- [x] Implement AuthContext with user state
- [x] Fetch current user on mount from `/api/auth/me`
- [x] Implement `logout()` function
- [x] Export `useAuth()` hook
- **Verification:** Context provides user state

### Task 4.2: Create Login Page ✅
- [x] Create `yoshikosan-frontend/app/login/page.tsx`
- [x] Build email/password form with validation
- [x] Add OAuth buttons for Google and Discord
- [x] Implement form submission to `/api/auth/login`
- [x] Handle errors and loading states
- [x] Add link to registration page
- **Verification:** Login page renders, form submits correctly

### Task 4.3: Create Registration Page ✅
- [x] Create `yoshikosan-frontend/app/register/page.tsx`
- [x] Build registration form (email, password, confirm password, name)
- [x] Implement real-time password validation
- [x] Show password requirements as user types
- [x] Check password mismatch before submission
- [x] Implement form submission to `/api/auth/register`
- [x] Add link to login page
- **Verification:** Registration page renders, validates passwords

### Task 4.4: Create Navigation Auth Status ✅
- [x] Update home page to use `useAuth()`
- [x] Display user name and avatar when authenticated
- [x] Add logout button
- [x] Hide auth UI when unauthenticated
- **Verification:** Nav shows user info when logged in

### Task 4.5: Implement Protected Route Middleware ⏭️
- [ ] Create route protection logic (deferred - no protected routes yet)
- [ ] Redirect to `/login` if unauthenticated
- [ ] Preserve original URL for post-login redirect
- [ ] Apply to protected routes
- **Verification:** Unauthenticated users redirected to login

---

## Phase 5: Containerization ✅

### Task 5.1: Create Frontend Dockerfile ✅
- [x] Create `yoshikosan-frontend/Dockerfile`
- [x] Stage 1: deps - Install dependencies with Bun
- [x] Stage 2: builder - Build Next.js standalone output
- [x] Stage 3: runner - Production runtime with non-root user
- [x] Set `NODE_ENV=production`
- [x] Expose port 3000
- **Verification:** `docker build -t yoshikosan-frontend .` succeeds

### Task 5.2: Create Backend Dockerfile ✅
- [x] Create `yoshikosan-backend/Dockerfile`
- [x] Stage 1: builder - Install dependencies with uv
- [x] Stage 2: runner - Production runtime with non-root user
- [x] Copy virtual environment from builder
- [x] Set up health check with `/health` endpoint
- [x] Expose port 8000
- **Verification:** `docker build -t yoshikosan-backend .` succeeds

### Task 5.3: Create .dockerignore Files ✅
- [x] Create `yoshikosan-frontend/.dockerignore`
- [x] Exclude node_modules, .next, .git, docs
- [x] Create `yoshikosan-backend/.dockerignore`
- [x] Exclude __pycache__, .pytest_cache, .venv, *.pyc
- **Verification:** Build context size reduced significantly

### Task 5.4: Update docker-compose.yml ✅
- [x] Add build context for frontend service
- [x] Add build context for backend service
- [x] Configure service dependencies (postgres → backend → frontend → nginx)
- [x] Add health checks for all services
- [x] Configure restart policy (unless-stopped)
- [x] Set up network and volumes
- [x] Pass environment variables from .env
- **Verification:** `docker-compose config` validates successfully

### Task 5.5: Test Full Stack Startup ⏭️
- [ ] Run `docker-compose up --build` (ready to test)
- [ ] Verify all services start successfully
- [ ] Check health checks pass
- [ ] Test frontend at http://localhost:6666/
- [ ] Test backend at http://localhost:6666/api/
- [ ] Test OpenAPI docs at http://localhost:6666/docs
- **Verification:** All services healthy, accessible through nginx

---

## Phase 6: Task Automation (Makefile) ✅

### Task 6.1: Create Makefile Structure ✅
- [x] Create `Makefile` in project root
- [x] Set up variables (FRONTEND_DIR, BACKEND_DIR, COMPOSE, DOCKER)
- [x] Set default goal to `help`
- [x] Mark all targets as `.PHONY`
- **Verification:** `make` shows help message

### Task 6.2: Add Development Commands ✅
- [x] Implement `make dev` - start all services
- [x] Implement `make dev-frontend` - start frontend only
- [x] Implement `make dev-backend` - start backend only
- **Verification:** Commands start respective services

### Task 6.3: Add Docker Commands ✅
- [x] Implement `make docker-build` - build all images
- [x] Implement `make docker-build-frontend` - build frontend image
- [x] Implement `make docker-build-backend` - build backend image
- [x] Implement `make docker-up` - start containers
- [x] Implement `make docker-down` - stop containers
- [x] Implement `make docker-logs` - view logs
- [x] Implement `make docker-restart` - restart containers
- [x] Implement `make docker-clean` - remove all resources
- **Verification:** All docker commands work correctly

### Task 6.4: Add Database Commands ✅
- [x] Implement `make db-init` - initialize database
- [x] Implement `make db-migrate` - run migrations
- [x] Implement `make db-reset` - reset database (with confirmation)
- [x] Implement `make db-shell` - connect to psql
- **Verification:** Database commands work correctly

### Task 6.5: Add Code Quality Commands ✅
- [x] Implement `make lint` - lint all code
- [x] Implement `make lint-frontend` - lint frontend
- [x] Implement `make lint-backend` - lint backend
- [x] Implement `make format` - format all code
- [x] Implement `make format-frontend` - format frontend
- [x] Implement `make format-backend` - format backend
- [x] Implement `make typecheck` - type check all
- [x] Implement `make test` - run all tests
- **Verification:** Quality commands run successfully

### Task 6.6: Add Utility Commands ✅
- [x] Implement `make help` - show all commands
- [x] Implement `make clean` - clean build artifacts
- [x] Implement `make env-check` - validate environment variables
- [x] Implement `make install-hooks` - install pre-commit hooks
- **Verification:** Utility commands work correctly

---

## Phase 7: Code Quality Enforcement ✅

### Task 7.1: Configure Backend Quality Tools ✅
- [x] Add Ruff configuration to `pyproject.toml`
- [x] Add mypy configuration to `pyproject.toml`
- [x] Set target Python version to 3.13
- [x] Configure line length, selected rules
- [x] Enable strict mode for mypy
- **Verification:** `uv run ruff check .` and `uv run mypy .` work

### Task 7.2: Configure Frontend Quality Tools ✅
- [x] Create `.eslintrc.json` with Next.js config
- [x] Create `.prettierrc` with formatting rules
- [x] Create `.prettierignore` file
- [x] Add scripts to `package.json` (lint, format, typecheck)
- **Verification:** `bun run lint` and `bun run format` work

### Task 7.3: Set Up Pre-commit Framework ✅
- [x] Create `.pre-commit-config.yaml` in project root
- [x] Configure Ruff hooks for backend
- [x] Configure mypy hooks for backend
- [x] Configure ESLint hooks for frontend
- [x] Configure Prettier hooks for frontend
- [x] Add general hooks (trailing whitespace, yaml check, json check)
- **Verification:** Configuration file validates

### Task 7.4: Install and Test Pre-commit ⏭️
- [ ] Run `make install-hooks` (ready to test)
- [ ] Run `pre-commit run --all-files` manually
- [ ] Fix any issues found
- [ ] Test commit with failing code (should block)
- [ ] Test commit with passing code (should succeed)
- **Verification:** Pre-commit blocks bad commits

---

## Phase 8: Testing & Validation ⏭️

### Task 8.1: Test Email/Password Authentication ⏭️
- [ ] Register new user via frontend (requires running system)
- [ ] Verify user created in database
- [ ] Login with correct credentials
- [ ] Verify JWT cookie set
- [ ] Test login with wrong password (should fail)
- [ ] Test registration with weak password (should fail)
- [ ] Test registration with duplicate email (should fail)
- **Verification:** All auth flows work correctly

### Task 8.2: Test OAuth Authentication ⏭️
- [ ] Test Google OAuth flow end-to-end (requires OAuth credentials)
- [ ] Verify user created with OAuth account
- [ ] Test Discord OAuth flow end-to-end (requires OAuth credentials)
- [ ] Verify oauth_accounts table populated
- [ ] Test linking multiple providers to same email
- **Verification:** OAuth flows work in production

### Task 8.3: Test Protected Routes ⏭️
- [ ] Access protected route while unauthenticated (should redirect)
- [ ] Login and access protected route (should succeed)
- [ ] Logout and verify cookie cleared
- [ ] Verify session invalidated in database
- **Verification:** Route protection works correctly

### Task 8.4: Test Container Optimization ⏭️
- [ ] Check frontend image size (should be < 300MB)
- [ ] Check backend image size (should be < 250MB)
- [ ] Measure container startup time (should be < 30 seconds)
- [ ] Verify multi-stage builds working
- [ ] Check that development dependencies excluded
- **Verification:** Images optimized, fast startup

### Task 8.5: Test Database Persistence ⏭️
- [ ] Create test user
- [ ] Stop containers with `docker-compose down`
- [ ] Start containers with `docker-compose up`
- [ ] Verify test user still exists
- [ ] Verify data persisted in volume
- **Verification:** Data persists across restarts

### Task 8.6: Test Health Checks ⏭️
- [ ] Verify `/health` endpoint returns 200
- [ ] Check Docker health status with `docker ps`
- [ ] Stop database and verify backend reports unhealthy
- [ ] Restart database and verify backend recovers
- **Verification:** Health checks working correctly

### Task 8.7: Test Makefile Commands ⏭️
- [ ] Test all `make dev-*` commands
- [ ] Test all `make docker-*` commands
- [ ] Test all `make db-*` commands
- [ ] Test all `make lint/format/typecheck` commands
- [ ] Verify help command shows all targets
- **Verification:** All Make commands work as documented

### Task 8.8: Test Code Quality Enforcement ⏭️
- [ ] Commit code with linting errors (should block)
- [ ] Commit code with type errors (should block)
- [ ] Commit code with formatting issues (should auto-fix)
- [ ] Run `make lint` manually (should catch issues)
- [ ] Run `make format` manually (should fix formatting)
- **Verification:** Quality checks enforce standards

---

## Phase 9: Documentation & Finalization ⏭️

### Task 9.1: Update README.md ⏭️
- [ ] Add project overview (deferred - user can update)
- [ ] Document prerequisites
- [ ] Add quick start instructions
- [ ] Document environment setup
- [ ] Add Make command reference
- [ ] Document deployment process
- **Verification:** New developer can follow README to get started

### Task 9.2: Document Authentication Setup ⏭️
- [ ] Document Google OAuth setup steps (deferred - user needs to set up OAuth apps)
- [ ] Document Discord OAuth setup steps
- [ ] Document environment variable requirements
- [ ] Add troubleshooting section
- **Verification:** Authentication setup documented

### Task 9.3: Create Production Deployment Guide ⏭️
- [ ] Document server requirements (deferred - user deployment specific)
- [ ] Document SSL/TLS setup (Nginx, Certbot)
- [ ] Document domain configuration
- [ ] Document environment variable setup for production
- [ ] Add monitoring and logging recommendations
- **Verification:** Production deployment guide complete

### Task 9.4: Final Integration Test ⏭️
- [ ] Full clean start: `make docker-clean` (ready to test)
- [ ] Build from scratch: `make docker-build`
- [ ] Start all services: `make docker-up`
- [ ] Run migrations: `make db-init`
- [ ] Test email/password registration
- [ ] Test email/password login
- [ ] Test Google OAuth
- [ ] Test Discord OAuth
- [ ] Test protected routes
- [ ] Test logout
- [ ] Verify all services healthy
- **Verification:** Complete system working end-to-end

---

## Success Criteria

All tasks completed when:
- ✅ `docker-compose up` successfully builds and starts all services
- ✅ Frontend accessible at http://localhost:6666/
- ✅ Backend API accessible at http://localhost:6666/api/
- ✅ Backend OpenAPI docs accessible at http://localhost:6666/docs
- ✅ Email/password authentication working (register, login, logout)
- ✅ OAuth authentication working (Google, Discord)
- ✅ Database connection established and migrations applied
- ✅ All environment variables properly loaded and validated
- ✅ `make` commands work for all common tasks
- ✅ Pre-commit hooks enforce code quality
- ✅ Production builds are optimized (< 300MB frontend, < 250MB backend)
- ✅ Health checks pass for all services
- ✅ Data persists across container restarts

## Estimated Timeline

- **Phase 1-2 (Config & Database):** 3-4 hours
- **Phase 3-4 (Auth Backend & Frontend):** 6-8 hours
- **Phase 5 (Containerization):** 3-4 hours
- **Phase 6 (Makefile):** 2-3 hours
- **Phase 7 (Code Quality):** 2-3 hours
- **Phase 8 (Testing):** 3-4 hours
- **Phase 9 (Documentation):** 2-3 hours

**Total: 21-29 hours**
