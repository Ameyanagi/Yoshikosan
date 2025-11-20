# Database Schema Spec

## ADDED Requirements

### Requirement: SOP Tables
**ID**: db-001
**Priority**: High
**Category**: Database Schema

The system SHALL define database tables for SOP storage.

#### Scenario: Create SOP-related tables
**Given** the database schema is being initialized
**When** the migration is executed
**Then** the following tables are created:
  - `sops` (id UUID, title TEXT, created_by UUID, created_at TIMESTAMP, updated_at TIMESTAMP, deleted_at TIMESTAMP)
  - `tasks` (id UUID, sop_id UUID, title TEXT, description TEXT, order_index INTEGER, created_at TIMESTAMP)
  - `steps` (id UUID, task_id UUID, description TEXT, order_index INTEGER, expected_action TEXT, expected_result TEXT)
  - `hazards` (id UUID, step_id UUID, description TEXT, severity TEXT, mitigation TEXT)
**And** foreign key constraints are established
**And** indexes are created for common queries
**And** TEXT columns are used for variable-length strings (no VARCHAR limits)

**Implementation**:
- Alembic migration: `alembic/versions/001_create_sop_tables.py`
- SQLAlchemy models: `src/infrastructure/database/models.py`
- Column types: Use `Text` for all string columns (title, description, severity, etc.)
- Constraints: CASCADE delete for task→sop, step→task, hazard→step
- Indexes: `idx_sops_user`, `idx_tasks_sop`, `idx_steps_task`

---

### Requirement: Work Session Tables
**ID**: db-002
**Priority**: High
**Category**: Database Schema

The system SHALL define database tables for work session tracking.

#### Scenario: Create session-related tables
**Given** the database schema is being initialized
**When** the migration is executed
**Then** the following tables are created:
  - `work_sessions` (id UUID, sop_id UUID, worker_id UUID, status TEXT, current_step_id UUID, started_at TIMESTAMP, completed_at TIMESTAMP, approved_at TIMESTAMP, approved_by UUID, locked BOOLEAN, rejection_reason TEXT)
  - `safety_checks` (id UUID, session_id UUID, step_id UUID, result TEXT, feedback_text TEXT, confidence_score FLOAT, needs_review BOOLEAN, checked_at TIMESTAMP, override_reason TEXT, override_by UUID)
**And** foreign key constraints link to SOPs, users, and steps
**And** indexes optimize session and check queries
**And** TEXT columns are used for all string data (status, URLs, feedback, transcripts)

**Implementation**:
- Alembic migration: `alembic/versions/002_create_session_tables.py`
- Column types: Use `Text` for all string columns (status, feedback_text, audio_transcript, URLs, etc.)
- Constraints: `sop_id→sops`, `worker_id→users`, `approved_by→users`
- Indexes: `idx_sessions_status`, `idx_sessions_worker`, `idx_checks_session`, `idx_checks_result`

---

### Requirement: Database Migrations
**ID**: db-003
**Priority**: High
**Category**: Infrastructure

The system SHALL use Alembic for database version control.

#### Scenario: Run initial migration
**Given** a fresh database instance
**When** `alembic upgrade head` is executed
**Then** all tables are created with correct schema
**And** the alembic_version table tracks the migration state

**Implementation**:
- Config: `alembic.ini` in backend root
- Migration dir: `alembic/versions/`
- Auto-generate: `alembic revision --autogenerate -m "description"`
- Rollback support: `alembic downgrade -1`

---

### Requirement: SQLAlchemy ORM Models
**ID**: db-004
**Priority**: High
**Category**: Infrastructure

The system SHALL define SQLAlchemy models matching the database schema.

#### Scenario: Map database tables to ORM models
**Given** the database schema is defined
**When** the application loads
**Then** SQLAlchemy models are available for queries
**And** relationships are defined (e.g., SOP.tasks, Task.steps)
**And** models support async operations

**Implementation**:
- Module: `src/infrastructure/database/models.py`
- Base: `from sqlalchemy.ext.asyncio import AsyncAttrs`
- Models: `SOPModel`, `TaskModel`, `StepModel`, `HazardModel`, `WorkSessionModel`, `SafetyCheckModel`
- Relationships: `relationship()` with `lazy="selectin"` for async

---

### Requirement: Database Session Management
**ID**: db-005
**Priority**: High
**Category**: Infrastructure

The system SHALL manage database connections using async sessions.

#### Scenario: Execute database query with session
**Given** a repository needs to query the database
**When** the session factory is used
**Then** an async database session is provided
**And** the session is automatically closed after use
**And** transactions are committed or rolled back appropriately

**Implementation**:
- Module: `src/infrastructure/database/session.py`
- Factory: `async def get_db_session() -> AsyncGenerator[AsyncSession, None]`
- Dependency injection in FastAPI: `Depends(get_db_session)`
- Config: Connection pool size, timeout settings

---

### Requirement: Soft Delete Support
**ID**: db-006
**Priority**: Medium
**Category**: Data Management

The system SHALL support soft deletion for audit trail preservation.

#### Scenario: Soft delete records with timestamp
**Given** a record needs to be deleted
**When** the soft delete is executed
**Then** the `deleted_at` field is set to current timestamp
**And** the record remains in the database
**And** queries filter out deleted records by default

**Implementation**:
- Add `deleted_at` column to relevant tables (sops)
- Repository methods: `WHERE deleted_at IS NULL`
- Delete method: `UPDATE SET deleted_at = NOW()`

---

### Requirement: Database Constraints
**ID**: db-007
**Priority**: High
**Category**: Data Integrity

The system SHALL enforce data integrity through database constraints.

#### Scenario: Enforce referential integrity
**Given** tables have foreign key relationships
**When** data is inserted or updated
**Then** foreign key constraints are validated
**And** invalid references are rejected
**And** cascade deletes work correctly

**Implementation**:
- All FK columns: `ForeignKey(..., ondelete="CASCADE")` where appropriate
- NOT NULL constraints on required fields
- UNIQUE constraints where needed (e.g., single active session per worker)
- CHECK constraints for enums (e.g., severity levels)
