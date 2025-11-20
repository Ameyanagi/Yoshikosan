"""Repository dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.infrastructure.database.repositories.session_repository import (
    SQLAlchemyWorkSessionRepository,
)
from src.infrastructure.database.repositories.sop_repository import (
    SQLAlchemySOPRepository,
)


def get_sop_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SQLAlchemySOPRepository:
    """Get SOP repository dependency.

    Args:
        db: Database session

    Returns:
        SOP repository instance
    """
    return SQLAlchemySOPRepository(db)


def get_session_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SQLAlchemyWorkSessionRepository:
    """Get WorkSession repository dependency.

    Args:
        db: Database session

    Returns:
        WorkSession repository instance
    """
    return SQLAlchemyWorkSessionRepository(db)
