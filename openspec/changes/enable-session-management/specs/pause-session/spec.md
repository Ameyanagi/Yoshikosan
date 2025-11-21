# pause-session Specification

## Purpose
Allow workers to temporarily pause work sessions and resume them later, enabling task switching without losing progress.

## ADDED Requirements

### Requirement: Pause Session Status

The system SHALL support a PAUSED status for work sessions.

**Rationale:** Workers need to temporarily stop work on a session and resume it later without completing all steps.

#### Scenario: Pause an in-progress session

**Given** a worker has a session with status "in_progress"
**And** the session has 3 completed safety checks
**And** the session is on step 4 of 10
**When** the worker pauses the session via POST /api/v1/sessions/{session_id}/pause
**Then** the session status SHALL change to "paused"
**And** the current_step_id SHALL remain at step 4
**And** all 3 safety checks SHALL be preserved
**And** the paused_at timestamp SHALL be recorded

#### Scenario: Cannot pause already completed session

**Given** a worker has a session with status "completed"
**When** the worker attempts to pause the session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Cannot pause a completed session"
**And** the session status SHALL remain "completed"

#### Scenario: Cannot pause already paused session

**Given** a worker has a session with status "paused"
**When** the worker attempts to pause the session again
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Session is already paused"

---

### Requirement: Resume Paused Session

The system SHALL allow resuming paused sessions back to in-progress status.

**Rationale:** Workers need to continue work on previously paused sessions.

#### Scenario: Resume a paused session

**Given** a worker has a session with status "paused"
**And** the session was paused at step 4 of 10
**And** the session has 3 completed checks
**When** the worker resumes the session via POST /api/v1/sessions/{session_id}/resume
**Then** the session status SHALL change to "in_progress"
**And** the current_step_id SHALL still be step 4
**And** all 3 safety checks SHALL be preserved
**And** the worker can add new safety checks

#### Scenario: Cannot resume non-paused session

**Given** a worker has a session with status "in_progress"
**When** the worker attempts to resume the session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Only paused sessions can be resumed"

#### Scenario: Cannot add checks to paused session

**Given** a worker has a session with status "paused"
**When** the worker attempts to execute a safety check for that session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Cannot add checks to a paused session"
**And** the session SHALL remain paused

---

### Requirement: Pause Session Authorization

Only the session owner SHALL be able to pause or resume their sessions.

**Rationale:** Prevent unauthorized users from interfering with worker sessions.

#### Scenario: Worker pauses their own session

**Given** a worker is authenticated as user ID "worker-123"
**And** a session exists owned by "worker-123"
**When** the worker pauses the session
**Then** the pause operation SHALL succeed
**And** the session SHALL be paused

#### Scenario: Cannot pause another worker's session

**Given** a worker is authenticated as user ID "worker-123"
**And** a session exists owned by "worker-456"
**When** worker-123 attempts to pause the session
**Then** the request SHALL fail with HTTP 403
**And** the error message SHALL state "Not authorized to modify this session"
**And** the session SHALL remain unchanged

#### Scenario: Supervisor can view paused sessions

**Given** a supervisor is authenticated
**And** a worker has a paused session
**When** the supervisor views the session details
**Then** the session SHALL be returned
**And** the status SHALL show "paused"
**And** the supervisor SHALL see all safety checks

---

### Requirement: List Paused Sessions

The system SHALL allow filtering sessions by paused status.

**Rationale:** Workers need to see which of their sessions are paused to decide which to resume.

#### Scenario: Filter sessions to show only paused

**Given** a worker has 2 sessions with status "in_progress"
**And** the worker has 3 sessions with status "paused"
**And** the worker has 1 session with status "completed"
**When** the worker requests GET /api/v1/sessions?status=paused
**Then** only the 3 paused sessions SHALL be returned
**And** sessions SHALL be ordered by paused_at descending

#### Scenario: Paused sessions appear in all sessions list

**Given** a worker has sessions with various statuses including "paused"
**When** the worker requests GET /api/v1/sessions without status filter
**Then** paused sessions SHALL be included in the response
**And** each session's status field SHALL accurately reflect "paused"

---

### Requirement: Domain Entity Pause Method

The WorkSession entity SHALL have a pause() method.

**Rationale:** Encapsulate pause logic in the domain entity following DDD principles.

#### Scenario: Entity pause method validates state

**Given** a WorkSession entity with status "in_progress"
**When** the pause() method is called
**Then** the status SHALL change to "paused"
**And** the locked flag SHALL remain false
**And** all checks SHALL be retained

#### Scenario: Entity prevents pausing locked sessions

**Given** a WorkSession entity with locked = true
**When** the pause() method is called
**Then** a ValueError SHALL be raised
**And** the error message SHALL state "Cannot modify a locked session"
**And** the status SHALL remain unchanged

#### Scenario: Entity prevents pausing completed sessions

**Given** a WorkSession entity with status "completed"
**When** the pause() method is called
**Then** a ValueError SHALL be raised
**And** the error message SHALL state "Can only pause in-progress sessions"
