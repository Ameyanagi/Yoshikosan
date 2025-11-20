# containerization Specification

## Purpose
TBD - created by archiving change add-production-deployment. Update Purpose after archive.
## Requirements
### Requirement: Frontend Production Dockerfile

The system SHALL provide a production-optimized Dockerfile for the Next.js frontend.

**Rationale:** Enable containerized deployment of the frontend with minimal image size and fast startup time.

#### Scenario: Multi-stage build for size optimization

**Given** the frontend Dockerfile uses multi-stage builds
**When** building the production image
**Then** the final image size SHALL be < 300MB
**And** the image SHALL only contain production dependencies
**And** the image SHALL exclude development tools and source files

#### Scenario: Bun 1.3 for package management

**Given** the frontend uses Bun 1.3 as the package manager
**When** installing dependencies in the Dockerfile
**Then** dependencies SHALL install 30x faster than npm
**And** the build SHALL use Bun's native TypeScript support
**And** the lockfile SHALL be bun.lock

#### Scenario: Next.js standalone output

**Given** the Next.js app is configured for standalone output
**When** building the production bundle
**Then** the output SHALL be a self-contained server
**And** the output SHALL be ~80% smaller than default build
**And** unnecessary files SHALL be excluded from the final image

#### Scenario: Non-root user execution

**Given** the container runs the Next.js server
**When** the container starts
**Then** the server process SHALL run as user `nextjs` (uid 1000)
**And** the server SHALL NOT run as root
**And** file permissions SHALL be properly set for the nextjs user

#### Scenario: Port 3000 exposure

**Given** the Next.js server runs in the container
**When** the container is running
**Then** the server SHALL listen on port 3000
**And** the port SHALL be exposed for internal Docker networking
**And** the NEXT_PUBLIC_API_URL SHALL be set to `/api`

---

### Requirement: Backend Production Dockerfile

The system SHALL provide a production-optimized Dockerfile for the FastAPI backend.

**Rationale:** Enable containerized deployment of the backend with minimal image size and fast startup time.

#### Scenario: Multi-stage build with uv

**Given** the backend Dockerfile uses multi-stage builds
**When** building the production image
**Then** the builder stage SHALL install dependencies using uv
**And** the runner stage SHALL only contain the virtual environment and source code
**And** the final image size SHALL be < 250MB

#### Scenario: Python 3.13 with slim base

**Given** the backend requires Python 3.13
**When** building the Dockerfile
**Then** the base image SHALL be `python:3.13-slim`
**And** the image SHALL use glibc (not musl) for better compatibility
**And** build tools SHALL be excluded from the final image

#### Scenario: uv for dependency management

**Given** the backend uses uv for package management
**When** installing dependencies in the Dockerfile
**Then** dependencies SHALL install 10-100x faster than pip
**And** the virtual environment SHALL be in `/opt/venv`
**And** the PATH SHALL include the venv binaries

#### Scenario: Non-root user execution

**Given** the container runs the FastAPI server
**When** the container starts
**Then** the server process SHALL run as user `appuser` (uid 1000)
**And** the server SHALL NOT run as root
**And** file permissions SHALL be properly set for the appuser

#### Scenario: Health check endpoint

**Given** the FastAPI server runs in the container
**When** the container is running
**Then** the server SHALL expose a `/health` endpoint
**And** the endpoint SHALL return 200 OK when healthy
**And** Docker health checks SHALL use this endpoint

#### Scenario: Port 8000 exposure

**Given** the FastAPI server runs in the container
**When** the container is running
**Then** the server SHALL listen on 0.0.0.0:8000
**And** the port SHALL be exposed for internal Docker networking
**And** uvicorn SHALL be configured for production

---

### Requirement: Docker Compose Orchestration

The system SHALL provide a complete docker-compose.yml configuration for all services.

**Rationale:** Enable single-command deployment of the entire stack with proper service dependencies and networking.

#### Scenario: Service dependency management

**Given** docker-compose.yml defines all services
**When** starting the services with `docker-compose up`
**Then** PostgreSQL SHALL start first
**And** the backend SHALL wait for PostgreSQL to be healthy
**And** the frontend SHALL start after backend
**And** Nginx SHALL start last after all services are ready

#### Scenario: Environment variable injection

**Given** environment variables are defined in `.env`
**When** docker-compose reads the configuration
**Then** all required variables SHALL be passed to respective containers
**And** missing required variables SHALL cause a clear error message
**And** optional variables SHALL use default values

#### Scenario: Network isolation

**Given** services run in Docker containers
**When** the services are started
**Then** all services SHALL be on the `yoshikosan-network` bridge network
**And** services SHALL communicate using service names (frontend, backend, postgres)
**And** only Nginx port 6666 SHALL be exposed to the host

#### Scenario: Volume persistence

**Given** PostgreSQL stores data
**When** containers are stopped and restarted
**Then** database data SHALL persist in the `postgres-data` volume
**And** data SHALL NOT be lost when containers are removed
**And** the volume SHALL be properly named

#### Scenario: Restart policy

**Given** containers may fail or crash
**When** a container exits unexpectedly
**Then** the container SHALL restart automatically
**And** the restart policy SHALL be `unless-stopped`
**And** manual stops SHALL NOT trigger automatic restart

---

### Requirement: Dockerignore Files

The system SHALL provide .dockerignore files to optimize build context.

**Rationale:** Reduce Docker build context size and improve build speed by excluding unnecessary files.

#### Scenario: Frontend dockerignore

**Given** the frontend Dockerfile builds the app
**When** Docker copies the build context
**Then** node_modules SHALL be excluded
**And** .next build artifacts SHALL be excluded
**And** .git directory SHALL be excluded
**And** documentation files SHALL be excluded

#### Scenario: Backend dockerignore

**Given** the backend Dockerfile builds the app
**When** Docker copies the build context
**Then** __pycache__ SHALL be excluded
**And** .pytest_cache SHALL be excluded
**And** .venv SHALL be excluded
**And** *.pyc files SHALL be excluded

