"""Password utilities for secure password hashing and validation."""

import re

from passlib.context import CryptContext

# Create password context with bcrypt (cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def validate_password(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets security requirements.

    Requirements:
    - Minimum 8 characters
    - Maximum 128 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number

    Args:
        password: Plain-text password to validate

    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []

    if len(password) < 8:
        errors.append("At least 8 characters")
    if len(password) > 128:
        errors.append("Maximum 128 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("One uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("One lowercase letter")
    if not re.search(r"\d", password):
        errors.append("One number")

    return len(errors) == 0, errors


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.

    Bcrypt has a 72-byte limit, so passwords are truncated to 72 bytes
    before hashing to avoid errors.

    Args:
        password: Plain-text password

    Returns:
        Hashed password string
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")[:72]
    password_truncated = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password_truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Truncates password to 72 bytes before verification to match hashing behavior.

    Args:
        plain_password: Plain-text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    # Truncate to 72 bytes (same as hash_password)
    password_bytes = plain_password.encode("utf-8")[:72]
    password_truncated = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(password_truncated, hashed_password)
