# Design: Production Deployment Infrastructure

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  External Proxy (HTTPS → HTTP)                              │
│  https://yoshikosan.ameyanagi.com                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Docker Host (http://host.docker.internal:6666)             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Nginx Container (Port 6666)                         │   │
│  │  - Path-based routing                                │   │
│  │  - / → Frontend                                      │   │
│  │  - /api/* → Backend (URL rewrite)                   │   │
│  └──────────────┬────────────────┬──────────────────────┘   │
│                 │                │                           │
│                 ↓                ↓                           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Frontend        │  │  Backend         │                │
│  │  Next.js 16      │  │  FastAPI         │                │
│  │  React 19        │  │  Python 3.13     │                │
│  │  Bun 1.3         │  │  uv              │                │
│  │  Port 3000       │  │  Port 8000       │                │
│  └──────────────────┘  └────────┬─────────┘                │
│                                  │                           │
│                                  ↓                           │
│                         ┌──────────────────┐                │
│                         │  PostgreSQL 16   │                │
│                         │  Port 5432       │                │
│                         └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Container Design

### Frontend Container (Next.js)

**Multi-stage Build Strategy:**

```dockerfile
Stage 1: Dependencies (deps)
- Base: node:20-alpine or oven/bun:1.3-alpine
- Install dependencies only
- Leverage layer caching

Stage 2: Builder
- Copy source code
- Build Next.js app
- Generate optimized production bundle

Stage 3: Runner (production)
- Minimal runtime image
- Copy built assets only
- Run Next.js in production mode
- Non-root user for security
```

**Key Decisions:**
- Use Bun 1.3 for faster install/build
- Standalone output for smaller image
- Multi-stage to exclude dev dependencies
- Alpine Linux for minimal size

### Backend Container (FastAPI)

**Multi-stage Build Strategy:**

```dockerfile
Stage 1: Builder
- Base: python:3.13-slim
- Install uv
- Create virtual environment
- Install dependencies with uv

Stage 2: Runner (production)
- Minimal python:3.13-slim image
- Copy venv from builder
- Copy source code
- Run uvicorn with proper config
- Non-root user for security
```

**Key Decisions:**
- Use uv for 10-100x faster installs
- Slim base image (not alpine - better Python compatibility)
- Virtual environment in /opt/venv
- Health check endpoint at /health

## Makefile Design

**Command Categories:**

```makefile
1. Development Commands
   - dev: Start both services in dev mode
   - dev-frontend: Start frontend only
   - dev-backend: Start backend only

2. Build Commands
   - build: Build both containers
   - build-frontend: Build frontend only
   - build-backend: Build backend only

3. Docker Commands
   - docker-up: Start all containers
   - docker-down: Stop all containers
   - docker-logs: View logs
   - docker-restart: Restart containers
   - docker-clean: Remove volumes and images

4. Database Commands
   - db-init: Initialize database
   - db-migrate: Run migrations
   - db-reset: Reset database
   - db-shell: Connect to PostgreSQL shell

5. Quality Commands
   - lint: Run linters
   - format: Format code
   - typecheck: Type checking
   - test: Run tests

6. Utility Commands
   - help: Show all commands
   - clean: Clean build artifacts
   - env-check: Validate .env file
```

## Environment Configuration

**Critical Environment Variables:**

```bash
# Deployment
DOMAIN=yoshikosan.ameyanagi.com
EXTERNAL_PORT=6666
NODE_ENV=production

# Database
DATABASE_URL=postgresql://yoshikosan:${POSTGRES_PASSWORD}@postgres:5432/yoshikosan_db

# Backend
SECRET_KEY=<generated-secret>
ALLOWED_ORIGINS=https://yoshikosan.ameyanagi.com

# OAuth (structure only, not implemented yet)
GOOGLE_CLIENT_ID=<from-google-console>
GOOGLE_CLIENT_SECRET=<from-google-console>
DISCORD_CLIENT_ID=<from-discord-dev>
DISCORD_CLIENT_SECRET=<from-discord-dev>

# AI Services
SAMBANOVA_API_KEY=<from-sambanova>
HUME_AI_API_KEY=<from-hume-ai>
```

## Build Optimization

### Frontend Optimizations
- Next.js standalone output (~80% size reduction)
- Bun for faster installs (30x vs npm)
- Static asset optimization
- Layer caching for dependencies
- `.dockerignore` to exclude unnecessary files

### Backend Optimizations
- uv for faster installs (10-100x vs pip)
- Multi-stage build (exclude build tools)
- Minimal slim base (not alpine for better Python compat)
- Pre-compiled Python bytecode
- Layer caching for dependencies

### Expected Image Sizes
- Frontend: ~200-300 MB (with Next.js standalone)
- Backend: ~150-250 MB (with Python slim)
- Total: ~350-550 MB (vs >1GB without optimization)

## Security Considerations

1. **Non-root Users**
   - Frontend runs as `nextjs` user
   - Backend runs as `appuser` user

2. **Secrets Management**
   - All secrets in `.env` (never committed)
   - OAuth secrets only in backend container

3. **Network Isolation**
   - Services on internal Docker network
   - Only Nginx port exposed externally

4. **Health Checks**
   - Backend: `/health` endpoint
   - PostgreSQL: `pg_isready` check
   - Nginx: HTTP 200 check

## Database Strategy

**Initialization:**
1. PostgreSQL starts with empty database
2. Backend waits for DB to be ready (health check)
3. Alembic migrations run on startup (if enabled)
4. Connection pooling configured for FastAPI

**Development vs Production:**
- Dev: Local SQLite or Docker PostgreSQL
- Prod: Docker PostgreSQL with persistent volume
- Connection string via `DATABASE_URL` env var

## Deployment Flow

```bash
1. Clone repository
2. Copy .env.example → .env
3. Edit .env with real credentials
4. Run: make docker-build
5. Run: make docker-up
6. Verify: curl http://localhost:6666/
7. Verify: curl http://localhost:6666/api/docs
```

## Monitoring & Logging

- **Container Logs:** `make docker-logs`
- **Health Checks:** Docker health check status
- **Restart Policy:** `unless-stopped` for resilience

## Trade-offs

| Decision | Pros | Cons | Rationale |
|----------|------|------|-----------|
| Multi-stage builds | Smaller images, faster deploys | More complex Dockerfiles | Production optimization critical |
| Bun for frontend | 30x faster than npm | Newer tool, less mature | Speed worth the risk |
| uv for backend | 10-100x faster than pip | Newer tool | Speed + built-in venv management |
| Slim vs Alpine | Better Python compatibility | Slightly larger | Python wheels need glibc |
| Nginx in Docker | Consistent environment | More containers | Simplifies deployment |

## Future Enhancements (Out of Scope)

- CI/CD pipeline (GitHub Actions)
- Image registry (Docker Hub, GHCR)
- Kubernetes manifests
- Monitoring (Prometheus, Grafana)
- Log aggregation (ELK stack)
- Secrets management (Vault, AWS Secrets Manager)
