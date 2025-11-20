"""Application settings and configuration."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file in project root (parent of yoshikosan-backend)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Deployment
    DOMAIN: str = Field(default="localhost")
    EXTERNAL_PORT: int = Field(default=6666)
    NODE_ENV: Literal["development", "production"] = Field(default="production")

    # Database
    POSTGRES_USER: str = Field(default="yoshikosan")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="yoshikosan_db")
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://yoshikosan:password@postgres:5432/yoshikosan_db"
    )

    # API
    SECRET_KEY: str = Field(default="")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    ALLOWED_ORIGINS: str = Field(default="https://yoshikosan.ameyanagi.com")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # OAuth
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    DISCORD_CLIENT_ID: str = Field(default="")
    DISCORD_CLIENT_SECRET: str = Field(default="")
    OAUTH_REDIRECT_URI: str = Field(
        default="https://yoshikosan.ameyanagi.com/auth/callback"
    )

    # AI Services - SambaNova
    SAMBANOVA_API_KEY: str = Field(default="")
    SAMBANOVA_MODEL: str = Field(default="Llama-4-Maverick-17B-128E-Instruct")
    SAMBANOVA_ENDPOINT: str = Field(
        default="https://api.sambanova.ai/v1/chat/completions"
    )
    SAMBANOVA_WHISPER_MODEL: str = Field(default="Whisper-Large-v3")
    SAMBANOVA_WHISPER_ENDPOINT: str = Field(
        default="https://api.sambanova.ai/v1/audio/transcriptions"
    )

    # AI Services - Hume AI
    HUME_AI_API_KEY: str = Field(default="")
    HUME_AI_SECRET_KEY: str = Field(default="")
    HUME_AI_ENDPOINT: str = Field(default="https://api.hume.ai/v0/tts/inference")
    HUME_AI_VOICE: str = Field(
        default="e5c30713-861d-476e-883a-fc0e1788f736"
    )  # Fumiko voice

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def cors_origins(self) -> list[str]:
        """Get parsed CORS origins."""
        origins = self.ALLOWED_ORIGINS
        if isinstance(origins, str):
            return [origin.strip() for origin in origins.split(",") if origin.strip()]
        return origins

    def validate_required(self) -> None:
        """Validate that required environment variables are set."""
        required_fields = {
            "SECRET_KEY": "Generate with: openssl rand -hex 32",
            "POSTGRES_PASSWORD": "Set a secure database password",
        }

        missing = []
        for field, hint in required_fields.items():
            value = getattr(self, field, "")
            if (
                not value
                or value
                == "your-secret-key-here-change-in-production-use-openssl-rand-hex-32"
            ):
                missing.append(f"  - {field}: {hint}")

        if missing and self.NODE_ENV == "production":
            raise ValueError(
                "Missing required environment variables:\n" + "\n".join(missing)
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


def configure_logging() -> None:
    """Configure logging with structured format."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
