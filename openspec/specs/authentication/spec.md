# authentication Specification

## Purpose
TBD - created by archiving change add-production-deployment. Update Purpose after archive.
## Requirements
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

