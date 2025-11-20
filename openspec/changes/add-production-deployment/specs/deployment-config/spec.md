# Spec: Deployment Configuration

**Capability:** deployment-config
**Status:** Draft
**Last Updated:** 2025-11-21

## Overview

Provide comprehensive deployment configuration including environment management, database initialization, health checks, and logging setup.

## ADDED Requirements

### Requirement: Environment Variable Management

The system SHALL provide comprehensive environment variable configuration with validation and documentation.

**Rationale:** Ensure all required configuration is properly set for production deployment with clear documentation.

#### Scenario: Complete env.example template

**Given** a new developer or deployment needs configuration
**When** viewing `.env.example`
**Then** all required variables SHALL be documented
**And** each variable SHALL have a comment explaining its purpose
**And** example values SHALL be provided where safe
**And** sensitive values SHALL show placeholder format

#### Scenario: Required variable validation

**Given** the application starts
**When** environment variables are loaded
**Then** all required variables SHALL be checked
**And** missing required variables SHALL cause startup failure
**And** the error message SHALL list all missing variables

#### Scenario: Environment-specific configurations

**Given** different deployment environments exist (dev, staging, prod)
**When** configuring environment variables
**Then** a template SHALL exist for each environment
**And** sensitive values SHALL never be committed
**And** `.env` files SHALL be gitignored

---

### Requirement: Database Configuration

The system SHALL provide database configuration for both development and production.

**Rationale:** Enable seamless database connectivity across different environments.

#### Scenario: PostgreSQL connection string format

**Given** the application needs to connect to PostgreSQL
**When** DATABASE_URL is configured
**Then** the format SHALL be `postgresql://user:password@host:port/database`
**And** the connection SHALL use the postgres service name in Docker
**And** SSL mode SHALL be configurable for production

#### Scenario: Connection pooling configuration

**Given** multiple requests may access the database
**When** the application connects to PostgreSQL
**Then** connection pooling SHALL be enabled
**And** pool size SHALL be configurable
**And** max overflow SHALL be configurable
**And** defaults SHALL be production-appropriate

#### Scenario: Database credentials security

**Given** database credentials are sensitive
**When** configuring the database
**Then** credentials SHALL be in environment variables only
**And** credentials SHALL never be in source code
**And** credentials SHALL never be logged

---

### Requirement: OAuth Configuration Structure

The system SHALL provide OAuth configuration structure for Google and Discord authentication.

**Rationale:** Prepare OAuth configuration for future authentication implementation.

#### Scenario: Google OAuth configuration

**Given** Google OAuth will be implemented
**When** configuring OAuth providers
**Then** GOOGLE_CLIENT_ID SHALL be required
**And** GOOGLE_CLIENT_SECRET SHALL be required
**And** OAuth redirect URI SHALL match Google Console configuration
**And** callback URL SHALL be https://yoshikosan.ameyanagi.com/api/auth/callback/google

#### Scenario: Discord OAuth configuration

**Given** Discord OAuth will be implemented
**When** configuring OAuth providers
**Then** DISCORD_CLIENT_ID SHALL be required
**And** DISCORD_CLIENT_SECRET SHALL be required
**And** OAuth redirect URI SHALL match Discord Developer Portal
**And** callback URL SHALL be https://yoshikosan.ameyanagi.com/api/auth/callback/discord

#### Scenario: OAuth scope documentation

**Given** OAuth requires specific scopes
**When** configuring OAuth
**Then** required scopes SHALL be documented in .env.example
**And** Google scopes SHALL include profile, email, openid
**And** Discord scopes SHALL include identify, email

---

### Requirement: AI Service Configuration

The system SHALL provide configuration for AI services (SambaNova, Hume AI).

**Rationale:** Enable AI-powered features with proper API key management.

#### Scenario: SambaNova API configuration

**Given** SambaNova provides LLM services
**When** configuring AI services
**Then** SAMBANOVA_API_KEY SHALL be required
**And** API endpoint SHALL be configurable
**And** model selection SHALL be configurable
**And** rate limits SHALL be respected

#### Scenario: Hume AI configuration

**Given** Hume AI provides empathic TTS
**When** configuring AI services
**Then** HUME_AI_API_KEY SHALL be required
**And** HUME_AI_SECRET_KEY SHALL be required
**And** voice model SHALL be configurable (default: "Fumiko")
**And** API endpoint SHALL be configurable

---

### Requirement: Health Check Configuration

The system SHALL provide health check endpoints and configuration.

**Rationale:** Enable monitoring and automated health verification of services.

#### Scenario: Backend health endpoint

**Given** the backend runs in a container
**When** accessing /health endpoint
**Then** the endpoint SHALL return 200 OK when healthy
**And** the response SHALL include service status
**And** the response SHALL include database connectivity status
**And** the response SHALL include timestamp

#### Scenario: Docker health check configuration

**Given** containers need health monitoring
**When** configuring docker-compose.yml
**Then** PostgreSQL SHALL have pg_isready health check
**And** backend SHALL have HTTP health check on /health
**And** health checks SHALL have appropriate intervals
**And** services SHALL wait for dependencies to be healthy

#### Scenario: Health check failure handling

**Given** a service fails its health check
**When** the health check fails repeatedly
**Then** the container SHALL be marked unhealthy
**And** dependent services SHALL not start
**And** logs SHALL indicate the failure reason

---

### Requirement: Logging Configuration

The system SHALL provide logging configuration for all services.

**Rationale:** Enable debugging and monitoring in production.

#### Scenario: Backend logging levels

**Given** the backend generates logs
**When** LOG_LEVEL is configured
**Then** levels SHALL include DEBUG, INFO, WARNING, ERROR
**And** production default SHALL be INFO
**And** development default SHALL be DEBUG
**And** log level SHALL be configurable via environment

#### Scenario: Structured logging format

**Given** logs need to be machine-readable
**When** the backend logs messages
**Then** logs SHALL be in JSON format
**And** logs SHALL include timestamp
**And** logs SHALL include log level
**And** logs SHALL include request context when available

#### Scenario: Docker logging drivers

**Given** containers generate logs
**When** configuring docker-compose.yml
**Then** logging driver SHALL be json-file
**And** logs SHALL have rotation configured
**And** max file size SHALL be limited
**And** max files SHALL be limited

---

### Requirement: CORS Configuration

The system SHALL provide CORS configuration for API security.

**Rationale:** Allow frontend to access backend API while maintaining security.

#### Scenario: Allowed origins configuration

**Given** the frontend needs to call the backend API
**When** configuring CORS
**Then** ALLOWED_ORIGINS SHALL include https://yoshikosan.ameyanagi.com
**And** localhost SHALL be allowed for development
**And** wildcard origins SHALL NOT be allowed in production
**And** origins SHALL be validated on startup

#### Scenario: CORS headers configuration

**Given** CORS is configured
**When** the backend responds to requests
**Then** appropriate CORS headers SHALL be set
**And** preflight requests SHALL be handled
**And** credentials SHALL be supported
**And** allowed methods SHALL be configured

---

### Requirement: Secret Key Management

The system SHALL provide secure secret key generation and management.

**Rationale:** Ensure cryptographic operations use secure, unique keys.

#### Scenario: JWT secret key requirements

**Given** JWT tokens need to be signed
**When** configuring SECRET_KEY
**Then** the key SHALL be at least 32 characters
**And** the key SHALL be cryptographically random
**And** the key SHALL be unique per deployment
**And** key generation instructions SHALL be documented

#### Scenario: Secret rotation support

**Given** secrets may need to be rotated
**When** SECRET_KEY changes
**Then** old tokens SHALL become invalid
**And** users SHALL need to re-authenticate
**And** the process SHALL be documented

## Implementation Notes

### Enhanced .env.example
```bash
# ==============================================================================
# DEPLOYMENT CONFIGURATION
# ==============================================================================
DOMAIN="yoshikosan.ameyanagi.com"
EXTERNAL_PORT="6666"
NODE_ENV="production"  # development | production

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
# PostgreSQL connection string for Docker
# Format: postgresql://username:password@host:port/database
POSTGRES_USER="yoshikosan"
POSTGRES_PASSWORD="your-secure-postgres-password-change-me"  # CHANGE THIS!
POSTGRES_DB="yoshikosan_db"
DATABASE_URL="postgresql://yoshikosan:your-secure-postgres-password@postgres:5432/yoshikosan_db"

# Database connection pool settings (optional)
DB_POOL_SIZE="5"
DB_MAX_OVERFLOW="10"

# Database port (for external access/debugging)
DB_EXTERNAL_PORT="5432"

# ==============================================================================
# BACKEND API CONFIGURATION (FastAPI)
# ==============================================================================
# Generate a secure secret key with: openssl rand -hex 32
SECRET_KEY="your-secret-key-here-change-in-production-use-openssl-rand-hex-32"
API_HOST="0.0.0.0"
API_PORT="8000"

# CORS - Allow requests from frontend
ALLOWED_ORIGINS="https://yoshikosan.ameyanagi.com"

# Logging
LOG_LEVEL="INFO"  # DEBUG | INFO | WARNING | ERROR

# ==============================================================================
# OAUTH PROVIDERS (Implementation pending)
# ==============================================================================
# Google OAuth - Get credentials from: https://console.cloud.google.com/apis/credentials
# Callback URL: https://yoshikosan.ameyanagi.com/api/auth/callback/google
# Required scopes: openid, profile, email
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-google-client-secret"

# Discord OAuth - Get credentials from: https://discord.com/developers/applications
# Callback URL: https://yoshikosan.ameyanagi.com/api/auth/callback/discord
# Required scopes: identify, email
DISCORD_CLIENT_ID="your-discord-client-id"
DISCORD_CLIENT_SECRET="your-discord-client-secret"

# OAuth Redirect URI (after successful authentication)
OAUTH_REDIRECT_URI="https://yoshikosan.ameyanagi.com/auth/callback"

# ==============================================================================
# AI SERVICES
# ==============================================================================
# SambaNova API - Get from: https://sambanova.ai
# Provides: Llama-4-Maverick-17B-128E-Instruct (multimodal vision+text)
# API Endpoint: https://api.sambanova.ai/v1
SAMBANOVA_API_KEY="your-sambanova-api-key"
SAMBANOVA_MODEL="Llama-4-Maverick-17B-128E-Instruct"  # optional

# Hume AI API - Get from: https://www.hume.ai
# Provides: Empathic TTS for emotionally intelligent voice feedback
# Voice Model: "Fumiko" (Japanese female voice)
# Docs: https://dev.hume.ai/docs/text-to-speech-tts/quickstart/typescript
HUME_AI_API_KEY="your-hume-ai-api-key"
HUME_AI_SECRET_KEY="your-hume-ai-secret-key"
HUME_AI_VOICE="Fumiko"  # optional

# ==============================================================================
# FRONTEND CONFIGURATION (Next.js)
# ==============================================================================
# API URL - Use relative path for same-origin requests (proxied by Nginx)
NEXT_PUBLIC_API_URL="/api"
PORT="3000"

# ==============================================================================
# HEALTH CHECK CONFIGURATION
# ==============================================================================
HEALTH_CHECK_INTERVAL="30s"
HEALTH_CHECK_TIMEOUT="10s"
HEALTH_CHECK_RETRIES="3"
```

### Backend Health Endpoint (FastAPI)
```python
from fastapi import FastAPI
from datetime import datetime

@app.get("/health")
async def health_check():
    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }
```

## Testing Requirements

1. **Variable Validation:** All required variables SHALL be validated on startup
2. **Health Checks:** All health check endpoints SHALL respond within timeout
3. **Database Connection:** Database connection SHALL succeed with valid credentials
4. **CORS:** Frontend SHALL successfully call backend API
5. **Logging:** Logs SHALL be generated in correct format

## Dependencies

- Python dotenv or Pydantic BaseSettings (backend)
- PostgreSQL client libraries
- FastAPI for health endpoints

## Related Specs

- `containerization` - Docker environment variable injection
- `automation` - Make commands for environment validation
