# Spec: Authentication Implementation

**Capability:** authentication
**Status:** Draft
**Last Updated:** 2025-11-21

## Overview

Provide comprehensive authentication implementation including email/password authentication, OAuth (Google and Discord), JWT token management, user database schema, and basic login UI.

## ADDED Requirements

### Requirement: User Database Schema

The system SHALL provide database schema for storing user authentication data.

**Rationale:** Enable persistent user accounts with OAuth provider linking.

#### Scenario: Users table structure

**Given** users need to be stored in the database
**When** creating the users table
**Then** the table SHALL have columns: id (UUID primary key), email (unique), name, avatar_url, password_hash (nullable), created_at, updated_at
**And** email SHALL be indexed for fast lookups
**And** id SHALL be auto-generated UUID
**And** password_hash SHALL be nullable (for OAuth-only users)
**And** password_hash SHALL use bcrypt hashing
**And** timestamps SHALL be automatically managed

#### Scenario: OAuth accounts table structure

**Given** users may link multiple OAuth providers
**When** creating the oauth_accounts table
**Then** the table SHALL have columns: id, user_id (foreign key), provider (google/discord), provider_user_id, access_token (encrypted), refresh_token (encrypted), expires_at, created_at
**And** (provider, provider_user_id) SHALL be unique
**And** user_id SHALL reference users table with CASCADE delete
**And** tokens SHALL be encrypted at rest

#### Scenario: Sessions table structure

**Given** users need authenticated sessions
**When** creating the sessions table
**Then** the table SHALL have columns: id (UUID), user_id (foreign key), token (hashed JWT), expires_at, created_at
**And** token SHALL be hashed with bcrypt
**And** expired sessions SHALL be automatically cleaned up
**And** user_id SHALL reference users table with CASCADE delete

---

### Requirement: OAuth Backend Implementation

The system SHALL provide FastAPI OAuth implementation for Google and Discord.

**Rationale:** Enable users to authenticate using their Google or Discord accounts.

#### Scenario: Google OAuth flow initiation

**Given** a user wants to login with Google
**When** accessing GET /api/auth/google
**Then** the user SHALL be redirected to Google OAuth consent page
**And** the redirect SHALL include client_id and redirect_uri
**And** the redirect SHALL request scopes: openid, profile, email
**And** a state parameter SHALL be included for CSRF protection

#### Scenario: Google OAuth callback handling

**Given** Google redirects back after user consent
**When** accessing GET /api/auth/callback/google with authorization code
**Then** the backend SHALL exchange code for access token
**And** the backend SHALL fetch user profile from Google
**And** the backend SHALL create or update user in database
**And** the backend SHALL create oauth_account record
**And** the backend SHALL generate JWT token
**And** the backend SHALL set HTTP-only cookie with JWT
**And** the backend SHALL redirect to frontend success page

#### Scenario: Discord OAuth flow initiation

**Given** a user wants to login with Discord
**When** accessing GET /api/auth/discord
**Then** the user SHALL be redirected to Discord OAuth authorization page
**And** the redirect SHALL include client_id and redirect_uri
**And** the redirect SHALL request scopes: identify, email
**And** a state parameter SHALL be included for CSRF protection

#### Scenario: Discord OAuth callback handling

**Given** Discord redirects back after user consent
**When** accessing GET /api/auth/callback/discord with authorization code
**Then** the backend SHALL exchange code for access token
**And** the backend SHALL fetch user profile from Discord API
**And** the backend SHALL create or update user in database
**And** the backend SHALL create oauth_account record
**And** the backend SHALL generate JWT token
**And** the backend SHALL set HTTP-only cookie with JWT
**And** the backend SHALL redirect to frontend success page

---

### Requirement: Email/Password Authentication

The system SHALL provide email/password authentication with secure password hashing and validation.

**Rationale:** Enable users to create accounts without OAuth providers.

#### Scenario: User registration

**Given** a user wants to register with email and password
**When** accessing POST /api/auth/register with email, password, and name
**Then** the email SHALL be validated for correct format
**And** the password SHALL be validated for minimum requirements (8+ characters, 1 uppercase, 1 lowercase, 1 number)
**And** the email SHALL be checked for uniqueness
**And** duplicate emails SHALL return 400 Bad Request
**And** the password SHALL be hashed using bcrypt with cost factor 12
**And** a new user record SHALL be created
**And** a JWT token SHALL be generated and returned
**And** the JWT SHALL be set as HTTP-only cookie

#### Scenario: User login

**Given** a user wants to login with email and password
**When** accessing POST /api/auth/login with email and password
**Then** the user SHALL be fetched by email
**And** the password SHALL be verified against stored hash
**And** incorrect email SHALL return 401 Unauthorized
**And** incorrect password SHALL return 401 Unauthorized
**And** successful login SHALL generate JWT token
**And** the JWT SHALL be set as HTTP-only cookie
**And** user data SHALL be returned (excluding password hash)

#### Scenario: Password security requirements

**Given** passwords need to be secure
**When** validating password requirements
**Then** minimum length SHALL be 8 characters
**And** maximum length SHALL be 128 characters
**And** password SHALL require at least 1 uppercase letter
**And** password SHALL require at least 1 lowercase letter
**And** password SHALL require at least 1 number
**And** password SHALL optionally allow special characters
**And** validation errors SHALL specify which requirements failed

#### Scenario: Password hashing

**Given** passwords need secure storage
**When** hashing a password
**Then** bcrypt algorithm SHALL be used
**And** cost factor SHALL be 12 (2^12 iterations)
**And** salt SHALL be generated automatically
**And** plain-text passwords SHALL never be stored
**And** plain-text passwords SHALL never be logged

---

### Requirement: JWT Token Management

The system SHALL provide JWT token generation, validation, and management.

**Rationale:** Enable secure, stateless authentication for API requests.

#### Scenario: JWT token generation

**Given** a user successfully authenticates
**When** generating a JWT token
**Then** the token SHALL include user_id in payload
**And** the token SHALL include email in payload
**And** the token SHALL include exp (expiration) claim
**And** the token SHALL be signed with SECRET_KEY
**And** the token SHALL expire in 7 days
**And** the token format SHALL be HS256

#### Scenario: JWT token validation

**Given** a request includes an Authorization header or cookie
**When** validating the JWT token
**Then** the signature SHALL be verified with SECRET_KEY
**And** the expiration SHALL be checked
**And** expired tokens SHALL be rejected with 401
**And** invalid signatures SHALL be rejected with 401
**And** valid tokens SHALL return user data

#### Scenario: Protected endpoint authentication

**Given** an API endpoint requires authentication
**When** a request is made to a protected endpoint
**Then** the JWT token SHALL be extracted from cookie or Authorization header
**And** the token SHALL be validated
**And** the user_id SHALL be available in the request context
**And** unauthenticated requests SHALL return 401 Unauthorized

---

### Requirement: Authentication Middleware

The system SHALL provide reusable authentication middleware for FastAPI.

**Rationale:** Standardize authentication checks across protected endpoints.

#### Scenario: get_current_user dependency

**Given** an endpoint requires authentication
**When** using get_current_user dependency
**Then** the dependency SHALL extract and validate JWT token
**And** the dependency SHALL fetch user from database
**And** the dependency SHALL return user object or raise 401
**And** the dependency SHALL be reusable across endpoints

#### Scenario: optional authentication

**Given** an endpoint supports both authenticated and anonymous users
**When** using get_current_user_optional dependency
**Then** the dependency SHALL return user if authenticated
**And** the dependency SHALL return None if not authenticated
**And** the dependency SHALL NOT raise 401 for missing token

---

### Requirement: User API Endpoints

The system SHALL provide user-related API endpoints for authentication status and logout.

**Rationale:** Enable frontend to check authentication status and perform logout.

#### Scenario: Get current user endpoint

**Given** a user is authenticated
**When** accessing GET /api/auth/me
**Then** the endpoint SHALL return user data (id, email, name, avatar)
**And** the endpoint SHALL require valid JWT token
**And** unauthenticated requests SHALL return 401

#### Scenario: Logout endpoint

**Given** a user wants to logout
**When** accessing POST /api/auth/logout
**Then** the JWT cookie SHALL be cleared
**And** the session SHALL be invalidated in database
**And** the response SHALL return 200 OK
**And** the user SHALL be logged out

---

### Requirement: Frontend Authentication UI

The system SHALL provide minimal authentication UI components.

**Rationale:** Enable users to initiate login and see authentication status.

#### Scenario: Login page with OAuth buttons

**Given** an unauthenticated user accesses the login page
**When** viewing /login
**Then** an email/password login form SHALL be displayed
**And** a "Login with Google" button SHALL be displayed
**And** a "Login with Discord" button SHALL be displayed
**And** clicking Google button SHALL redirect to /api/auth/google
**And** clicking Discord button SHALL redirect to /api/auth/discord
**And** a link to /register page SHALL be displayed

#### Scenario: Registration page

**Given** a user wants to create a new account
**When** viewing /register
**Then** a registration form SHALL be displayed
**And** the form SHALL have fields: email, password, confirm password, name
**And** the form SHALL validate password requirements in real-time
**And** password mismatch SHALL be shown before submission
**And** successful registration SHALL redirect to home page
**And** a link to /login page SHALL be displayed

#### Scenario: Authentication status indicator

**Given** the application has a navigation bar
**When** a user is authenticated
**Then** the user's name and avatar SHALL be displayed
**And** a "Logout" button SHALL be available
**And** clicking logout SHALL call /api/auth/logout

#### Scenario: Protected route handling

**Given** certain routes require authentication
**When** an unauthenticated user accesses a protected route
**Then** the user SHALL be redirected to /login
**And** the original URL SHALL be preserved for redirect after login

---

### Requirement: Database Migrations

The system SHALL provide Alembic migrations for authentication schema.

**Rationale:** Enable version-controlled database schema changes.

#### Scenario: Initial authentication migration

**Given** the database is empty
**When** running initial migration
**Then** users table SHALL be created
**And** oauth_accounts table SHALL be created
**And** sessions table SHALL be created
**And** appropriate indexes SHALL be created
**And** foreign key constraints SHALL be established

#### Scenario: Migration rollback support

**Given** a migration has been applied
**When** rolling back the migration
**Then** all tables SHALL be dropped in correct order
**And** foreign key constraints SHALL be removed first
**And** the database SHALL return to previous state

## Implementation Notes

### SQLAlchemy Models (Backend)

```python
# src/domain/user/entities.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # Nullable for OAuth-only users
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        Index("ix_oauth_provider_user", "provider", "provider_user_id", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    provider = Column(String, nullable=False)  # 'google' or 'discord'
    provider_user_id = Column(String, nullable=False)
    access_token = Column(String, nullable=False)  # encrypted
    refresh_token = Column(String, nullable=True)  # encrypted
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="oauth_accounts")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")
```

### Password Utilities (Backend)

```python
# src/domain/user/password.py
import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_password(password: str) -> tuple[bool, list[str]]:
    """Validate password meets security requirements."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    
    return len(errors) == 0, errors

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### Authentication Endpoints (Backend)

```python
# src/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
import httpx
from jose import jwt
from datetime import datetime, timedelta
from src.domain.user.password import validate_password, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with email and password"""
    # Validate password
    is_valid, errors = validate_password(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # Check if email already exists
    existing_user = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
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
    
    # Set cookie
    response = Response(content={"message": "Registration successful"})
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response

@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    # Fetch user
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and has password
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})
    
    # Set cookie and return user data
    response = Response(content={
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
    })
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response

@router.get("/google")
async def google_login():
    """Initiate Google OAuth flow"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.OAUTH_REDIRECT_URI}/google"
        f"&response_type=code"
        f"&scope=openid%20profile%20email"
        f"&state={generate_state_token()}"
    )
    return RedirectResponse(google_auth_url)

@router.get("/callback/google")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{settings.OAUTH_REDIRECT_URI}/google",
                "grant_type": "authorization_code",
            },
        )
        tokens = token_response.json()

        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_info = user_response.json()

    # Create or update user
    user = await get_or_create_user(db, user_info, "google")

    # Generate JWT
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

    # Set cookie and redirect
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )
    return response

@router.get("/discord")
async def discord_login():
    """Initiate Discord OAuth flow"""
    # Similar to Google but with Discord endpoints
    pass

@router.get("/callback/discord")
async def discord_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Discord OAuth callback"""
    # Similar to Google callback
    pass

@router.get("/me")
async def get_current_user(user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
    }

@router.post("/logout")
async def logout(response: Response, user: User = Depends(get_current_user)):
    """Logout current user"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
```

### Frontend Login Component (Next.js)

```tsx
// app/(public)/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Login failed");
      }

      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 rounded-lg border p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Welcome to ヨシコさん、ヨシッ！</h1>
          <p className="mt-2 text-gray-600">Sign in to continue</p>
        </div>

        {/* Email/Password Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border px-4 py-2"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border px-4 py-2"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-white px-2 text-gray-500">Or continue with</span>
          </div>
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-3">
          <a
            href="/api/auth/google"
            className="flex w-full items-center justify-center gap-3 rounded-lg border bg-white px-4 py-3 font-medium hover:bg-gray-50"
          >
            <GoogleIcon />
            Continue with Google
          </a>

          <a
            href="/api/auth/discord"
            className="flex w-full items-center justify-center gap-3 rounded-lg border bg-[#5865F2] px-4 py-3 font-medium text-white hover:bg-[#4752C4]"
          >
            <DiscordIcon />
            Continue with Discord
          </a>
        </div>

        <p className="text-center text-sm text-gray-600">
          Don't have an account?{" "}
          <Link href="/register" className="font-medium text-blue-600 hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
```

### Frontend Registration Component (Next.js)

```tsx
// app/(public)/register/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    name: "",
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const validatePassword = (password: string): string[] => {
    const errors: string[] = [];
    if (password.length < 8) errors.push("At least 8 characters");
    if (!/[A-Z]/.test(password)) errors.push("One uppercase letter");
    if (!/[a-z]/.test(password)) errors.push("One lowercase letter");
    if (!/\d/.test(password)) errors.push("One number");
    return errors;
  };

  const passwordErrors = validatePassword(formData.password);
  const passwordMismatch = formData.password !== formData.confirmPassword && formData.confirmPassword !== "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);
    setLoading(true);

    if (passwordErrors.length > 0) {
      setErrors(passwordErrors);
      setLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setErrors(["Passwords do not match"]);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          name: formData.name,
        }),
        credentials: "include",
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Registration failed");
      }

      router.push("/");
    } catch (err) {
      setErrors([err instanceof Error ? err.message : "Registration failed"]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8 rounded-lg border p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Create an account</h1>
          <p className="mt-2 text-gray-600">Join ヨシコさん、ヨシッ！</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium">
              Name
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="mt-1 w-full rounded-lg border px-4 py-2"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              className="mt-1 w-full rounded-lg border px-4 py-2"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              className="mt-1 w-full rounded-lg border px-4 py-2"
            />
            {formData.password && passwordErrors.length > 0 && (
              <ul className="mt-1 text-xs text-red-600">
                {passwordErrors.map((err, i) => (
                  <li key={i}>• {err}</li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              required
              className="mt-1 w-full rounded-lg border px-4 py-2"
            />
            {passwordMismatch && (
              <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
            )}
          </div>

          {errors.length > 0 && (
            <div className="rounded-lg bg-red-50 p-3">
              {errors.map((err, i) => (
                <p key={i} className="text-sm text-red-600">{err}</p>
              ))}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || passwordErrors.length > 0 || passwordMismatch}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Sign up"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-blue-600 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
```

### Auth Context Provider (Frontend)

```tsx
// lib/auth-context.tsx
"use client";

import { createContext, useContext, useState, useEffect } from "react";

type User = {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
} | null;

const AuthContext = createContext<{
  user: User;
  loading: boolean;
  logout: () => Promise<void>;
}>({
  user: null,
  loading: true,
  logout: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setUser(data))
      .finally(() => setLoading(false));
  }, []);

  const logout = async () => {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

## Testing Requirements

1. **Email/Password Registration:** User SHALL be able to register with email and password
2. **Email/Password Login:** User SHALL be able to login with correct credentials
3. **Password Validation:** Invalid passwords SHALL be rejected with clear error messages
4. **OAuth Flow:** Complete OAuth flow SHALL work for both Google and Discord
5. **JWT Tokens:** Generated tokens SHALL be valid and verifiable
6. **Database:** User and session data SHALL persist correctly
7. **Protected Routes:** Unauthenticated access SHALL be blocked
8. **Logout:** Logout SHALL clear cookies and invalidate sessions
9. **Password Security:** Plain-text passwords SHALL never be stored or logged

## Dependencies

- FastAPI Security utilities
- python-jose (JWT)
- passlib[bcrypt] (password hashing)
- httpx (OAuth HTTP requests)
- SQLAlchemy 2.0 (async)
- Alembic (migrations)
- React Context API (frontend state)
- Pydantic (request validation)

## Related Specs

- `deployment-config` - OAuth environment variables
- `containerization` - Backend with auth dependencies
