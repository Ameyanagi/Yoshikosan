# Work Session Management Spec

## ADDED Requirements

### Requirement: Session Creation
**ID**: session-001
**Priority**: High
**Category**: Core Feature

The system SHALL allow workers to start new work sessions from confirmed SOPs.

#### Scenario: Start work session from SOP
**Given** a user has a confirmed SOP
**When** they start a new work session
**Then** a session record is created with status "in_progress"
**And** the current step is set to the first step of the first task
**And** the session is linked to the SOP and worker
**And** a start timestamp is recorded

**Implementation**:
- Endpoint: `POST /api/v1/sessions`
- Request: `{sop_id: UUID}`
- Use case: `src/application/work_session/start_session.py`
- Domain: `src/domain/work_session/entities.py` - `WorkSession` aggregate
- Initial state: `status=IN_PROGRESS`, `current_step_id=first_step_id`, `started_at=NOW()`

---

### Requirement: Session State Management
**ID**: session-002
**Priority**: High
**Category**: Core Feature

The system SHALL track session progress through SOP steps.

#### Scenario: Advance to next step after passed check
**Given** a work session is in progress
**And** a safety check passed for the current step
**When** the session is updated
**Then** the current_step_id advances to the next step
**And** the session status remains "in_progress"
**And** the next step is returned to the client

**Implementation**:
- Domain method: `WorkSession.advance_to_next_step(next_step_id)`
- Use case handles step lookup (query SOP for next step)
- Update `current_step_id` in database
- If no next step (end of SOP), trigger completion

---

#### Scenario: Complete session after final step
**Given** a work session is on the last step
**And** the final safety check passes
**When** the session is updated
**Then** the status changes to "completed"
**And** the completed_at timestamp is set
**And** the current_step_id is set to null

**Implementation**:
- Domain method: `WorkSession.complete()`
- Set `status=COMPLETED`, `completed_at=NOW()`, `current_step_id=NULL`
- Emit domain event: `WorkSessionCompleted`

---

### Requirement: Session Retrieval
**ID**: session-003
**Priority**: Medium
**Category**: User Experience

The system SHALL provide endpoints to retrieve session details and history.

#### Scenario: Get active session for worker
**Given** a worker has an active session
**When** they request their current session
**Then** the in-progress session is returned with current step
**And** all completed checks are included
**And** the next expected step is indicated

**Implementation**:
- Endpoint: `GET /api/v1/sessions/current`
- Query: `status=IN_PROGRESS AND worker_id={current_user}`
- Response: Full session with SOP details, checks, current step

---

#### Scenario: List worker's session history
**Given** a worker is authenticated
**When** they request their session list
**Then** all their sessions are returned (completed + in-progress)
**And** sessions are ordered by most recent first
**And** basic session info is included (SOP title, status, timestamps)

**Implementation**:
- Endpoint: `GET /api/v1/sessions`
- Query params: `status` (optional filter), `limit`, `offset`
- Order: `started_at DESC`

---

### Requirement: Session Completion
**ID**: session-004
**Priority**: High
**Category**: Core Feature

The system SHALL allow manual session completion.

#### Scenario: Worker completes session manually
**Given** a work session is in progress
**And** the worker has finished the work
**When** they mark the session as complete
**Then** the session status changes to "completed"
**And** the completion timestamp is recorded
**And** the session can no longer be modified (except by supervisor override)

**Implementation**:
- Endpoint: `POST /api/v1/sessions/{id}/complete`
- Domain method: `WorkSession.complete()`
- Authorization: Only session owner can complete

---

### Requirement: Session Immutability After Approval
**ID**: session-005
**Priority**: High
**Category**: Data Integrity

The system SHALL prevent modification of approved sessions.

#### Scenario: Attempt to modify locked session
**Given** a work session is approved
**And** the locked flag is true
**When** any modification is attempted
**Then** an error is raised
**And** the modification is rejected
**And** an audit log entry is created

**Implementation**:
- Domain method: All mutation methods check `if self.locked: raise ValueError(...)`
- Applied to: `add_check()`, `advance_to_next_step()`, `complete()`
- HTTP 409 Conflict response

---

### Requirement: Session-SOP Relationship
**ID**: session-006
**Priority**: High
**Category**: Domain Design

The system SHALL maintain referential integrity between sessions and SOPs.

#### Scenario: Prevent SOP deletion with active sessions
**Given** an SOP has active work sessions
**When** deletion is attempted
**Then** the deletion is blocked
**And** an error message lists the active sessions
**And** the user is advised to complete or cancel sessions first

**Implementation**:
- Check in `DeleteSOPUseCase`
- Query: `COUNT(*) FROM work_sessions WHERE sop_id={id} AND status='in_progress'`
- If count > 0, raise validation error
- HTTP 400 Bad Request

---

### Requirement: Session Repository
**ID**: session-007
**Priority**: High
**Category**: Infrastructure

The system SHALL provide a repository for work session persistence.

#### Scenario: Save session with checks
**Given** a work session aggregate with safety checks
**When** the repository save method is called
**Then** the session and all checks are persisted atomically
**And** relationships are maintained

**Implementation**:
- Protocol: `src/domain/work_session/repositories.py` - `WorkSessionRepository`
- Implementation: `src/infrastructure/database/repositories/session_repository.py`
- Methods: `save(session: WorkSession)`, `get_by_id(id: UUID)`, `get_current_for_worker(worker_id: UUID)`, `list_by_worker(worker_id: UUID)`

---

### Requirement: Session Pause and Resume (Future)
**ID**: session-008
**Priority**: Low
**Category**: Future Enhancement

The system SHALL support pausing and resuming work sessions in future versions.

#### Scenario: Worker pauses session
**Given** a work session is in progress
**When** the worker pauses the session
**Then** the status changes to "paused"
**And** the pause timestamp is recorded
**And** the current step is preserved

**Implementation**:
- Add `paused_at` field to `work_sessions`
- Add `PAUSED` status to enum
- Endpoint: `POST /api/v1/sessions/{id}/pause`
- Out of scope for MVP

---

### Requirement: Concurrent Session Handling
**ID**: session-009
**Priority**: Medium
**Category**: Business Rules

The system SHALL prevent workers from having multiple active sessions simultaneously.

#### Scenario: Start session while one is active
**Given** a worker has an active session
**When** they attempt to start a new session
**Then** the request is rejected
**And** an error message references the existing session
**And** the user is prompted to complete or cancel the active session

**Implementation**:
- Check in `StartSessionUseCase`
- Query for existing active session
- HTTP 409 Conflict if found
- Return existing session ID in error response
