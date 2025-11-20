"""Database base class."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Import all models here for Alembic autogenerate
from src.domain.user.entities import OAuthAccount, Session, User  # noqa: E402, F401
