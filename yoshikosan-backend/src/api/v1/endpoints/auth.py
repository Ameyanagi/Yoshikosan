"""Authentication endpoints."""

import secrets
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user
from src.config import settings
from src.db.session import get_db
from src.domain.user.entities import OAuthAccount, User
from src.domain.user.jwt import create_access_token
from src.domain.user.password import hash_password, validate_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Request/Response Models
# ============================================================================


class RegisterRequest(BaseModel):
    """Registration request model."""

    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: str
    name: str
    avatar_url: str | None


# ============================================================================
# Email/Password Authentication
# ============================================================================


@router.post("/register", response_model=UserResponse)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user with email and password.

    Validates password requirements, checks for duplicate emails,
    creates user with hashed password, and returns JWT cookie.
    """
    # Validate password
    is_valid, errors = validate_password(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors},
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.NODE_ENV == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
    )


@router.post("/login", response_model=UserResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login with email and password.

    Verifies credentials, generates JWT, and sets HTTP-only cookie.
    """
    # Fetch user
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Verify user exists and has password
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.NODE_ENV == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
    )


# ============================================================================
# OAuth - Google
# ============================================================================


@router.get("/google")
async def google_login(request: Request) -> RedirectResponse:
    """Initiate Google OAuth flow."""
    state = secrets.token_urlsafe(32)

    # Build redirect URI from request headers
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get(
        "x-forwarded-host", request.headers.get("host", request.url.netloc)
    )
    redirect_uri = f"{scheme}://{host}/api/auth/callback/google"

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20profile%20email"
        f"&state={state}"
    )

    return RedirectResponse(google_auth_url)


@router.get("/callback/google")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Google OAuth callback."""
    # Build redirect URI from request headers (must match the one sent to Google)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get(
        "x-forwarded-host", request.headers.get("host", request.url.netloc)
    )
    redirect_uri = f"{scheme}://{host}/api/auth/callback/google"

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            return RedirectResponse(url="/?error=oauth_failed")

        tokens = token_response.json()

        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        if user_response.status_code != 200:
            return RedirectResponse(url="/?error=oauth_failed")

        user_info = user_response.json()

    # Find or create user
    email = user_info.get("email")
    if not email:
        return RedirectResponse(url="/?error=no_email")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            name=user_info.get("name", email.split("@")[0]),
            avatar_url=user_info.get("picture"),
        )
        db.add(user)
        await db.flush()

    # Create or update OAuth account
    oauth_result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_user_id == user_info["id"],
        )
    )
    oauth_account = oauth_result.scalar_one_or_none()

    if not oauth_account:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_user_id=user_info["id"],
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_at=datetime.utcnow(),
        )
        db.add(oauth_account)
    else:
        oauth_account.access_token = tokens["access_token"]
        if tokens.get("refresh_token"):
            oauth_account.refresh_token = tokens["refresh_token"]

    await db.commit()

    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

    # Set cookie and redirect
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.NODE_ENV == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response


# ============================================================================
# OAuth - Discord
# ============================================================================


@router.get("/discord")
async def discord_login(request: Request) -> RedirectResponse:
    """Initiate Discord OAuth flow."""
    state = secrets.token_urlsafe(32)

    # Build redirect URI from request headers
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get(
        "x-forwarded-host", request.headers.get("host", request.url.netloc)
    )
    redirect_uri = f"{scheme}://{host}/api/auth/callback/discord"

    discord_auth_url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=identify%20email"
        f"&state={state}"
    )

    return RedirectResponse(discord_auth_url)


@router.get("/callback/discord")
async def discord_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Discord OAuth callback."""
    # Build redirect URI from request headers (must match the one sent to Discord)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get(
        "x-forwarded-host", request.headers.get("host", request.url.netloc)
    )
    redirect_uri = f"{scheme}://{host}/api/auth/callback/discord"

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "code": code,
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_response.status_code != 200:
            return RedirectResponse(url="/?error=oauth_failed")

        tokens = token_response.json()

        # Get user info
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        if user_response.status_code != 200:
            return RedirectResponse(url="/?error=oauth_failed")

        user_info = user_response.json()

    # Find or create user
    email = user_info.get("email")
    if not email:
        return RedirectResponse(url="/?error=no_email")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        avatar_hash = user_info.get("avatar")
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{user_info['id']}/{avatar_hash}.png"
            if avatar_hash
            else None
        )

        user = User(
            email=email,
            name=user_info.get("username", email.split("@")[0]),
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.flush()

    # Create or update OAuth account
    oauth_result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == "discord",
            OAuthAccount.provider_user_id == user_info["id"],
        )
    )
    oauth_account = oauth_result.scalar_one_or_none()

    if not oauth_account:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider="discord",
            provider_user_id=user_info["id"],
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_at=datetime.utcnow(),
        )
        db.add(oauth_account)
    else:
        oauth_account.access_token = tokens["access_token"]
        if tokens.get("refresh_token"):
            oauth_account.refresh_token = tokens["refresh_token"]

    await db.commit()

    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

    # Set cookie and redirect
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.NODE_ENV == "production",
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response


# ============================================================================
# User Management
# ============================================================================


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> Any:
    """Get current authenticated user."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Logout current user by clearing cookie."""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
