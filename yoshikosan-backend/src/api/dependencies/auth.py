"""Authentication dependencies."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.domain.user.entities import User
from src.domain.user.jwt import verify_token


async def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Extracts JWT from cookie, validates it, and fetches user from database.
    Raises 401 if token is invalid or user not found.

    Args:
        access_token: JWT token from cookie
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: 401 Unauthorized if token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not access_token:
        raise credentials_exception

    # Verify and decode token
    payload = verify_token(access_token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    access_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get current authenticated user, or None if not authenticated.

    Similar to get_current_user but returns None instead of raising exception.
    Useful for endpoints that support both authenticated and anonymous access.

    Args:
        access_token: JWT token from cookie
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not access_token:
        return None

    # Verify and decode token
    payload = verify_token(access_token)
    if payload is None:
        return None

    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    return user
