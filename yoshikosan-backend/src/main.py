"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.v1.endpoints import audit, auth, check, session, sop
from src.config import settings
from src.db.session import AsyncSessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan events."""
    # Startup
    logger.info("Starting ヨシコさん、ヨシッ！Backend API")
    logger.info(f"Environment: {settings.NODE_ENV}")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Validate required settings
    try:
        settings.validate_required()
        logger.info("✓ Configuration validated")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        if settings.NODE_ENV == "production":
            raise

    yield

    # Shutdown
    logger.info("Shutting down ヨシコさん、ヨシッ！Backend API")


# Create FastAPI application
app = FastAPI(
    title="ヨシコさん、ヨシッ！API",
    description="Industrial Safety Management System Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(sop.router, prefix="/api/v1")
app.include_router(session.router, prefix="/api/v1")
app.include_router(check.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "ヨシコさん、ヨシッ！API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint with database connectivity verification."""
    # Check database connectivity
    db_status = "healthy"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    overall_status = "healthy" if db_status == "healthy" else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.NODE_ENV == "development",
    )
