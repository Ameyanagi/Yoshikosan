# abort-session Specification

## Purpose
Allow workers to permanently cancel unwanted sessions while retaining safety check data for audit purposes.

## ADDED Requirements

### Requirement: Abort Session Status

The system SHALL support an ABORTED status for work sessions.

**Rationale:** Workers may start a session by mistake or need to cancel it due to equipment failure or other circumstances. Aborted sessions must retain audit data but be excluded from normal workflows.

#### Scenario: Abort an in-progress session

**Given** a worker has a session with status "in_progress"
**And** the session has 2 completed safety checks
**And** the session is on step 3 of 10
**When** the worker aborts the session via POST /api/v1/sessions/{session_id}/abort
**Then** the session status SHALL change to "aborted"
**And** all 2 safety checks SHALL be preserved
**And** the aborted_at timestamp SHALL be recorded
**And** the abort_reason SHALL be stored if provided

#### Scenario: Abort a paused session

**Given** a worker has a session with status "paused"
**When** the worker aborts the session
**Then** the session status SHALL change to "aborted"
**And** all progress SHALL be preserved for audit
**And** the aborted_at timestamp SHALL be recorded

#### Scenario: Cannot abort completed session

**Given** a worker has a session with status "completed"
**When** the worker attempts to abort the session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Cannot abort a completed session"
**And** the session status SHALL remain "completed"

#### Scenario: Cannot abort already aborted session

**Given** a worker has a session with status "aborted"
**When** the worker attempts to abort the session again
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Session is already aborted"

---

### Requirement: Abort Reason Tracking

The system SHALL optionally record a reason when aborting a session.

**Rationale:** Understanding why sessions are aborted helps identify systemic issues and training needs.

#### Scenario: Abort session with reason

**Given** a worker has a session with status "in_progress"
**When** the worker aborts the session with reason "Equipment malfunction"
**Then** the session status SHALL change to "aborted"
**And** the abort_reason SHALL be "Equipment malfunction"
**And** the aborted_at timestamp SHALL be recorded

#### Scenario: Abort session without reason

**Given** a worker has a session with status "in_progress"
**When** the worker aborts the session without providing a reason
**Then** the session status SHALL change to "aborted"
**And** the abort_reason SHALL be null
**And** the operation SHALL succeed

---

### Requirement: Aborted Session Cannot Be Modified

Aborted sessions SHALL be immutable and cannot be resumed or modified.

**Rationale:** Maintain audit trail integrity by preventing changes to aborted sessions.

#### Scenario: Cannot resume aborted session

**Given** a worker has a session with status "aborted"
**When** the worker attempts to resume the session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Cannot resume an aborted session"
**And** the session SHALL remain aborted

#### Scenario: Cannot add checks to aborted session

**Given** a worker has a session with status "aborted"
**When** the worker attempts to execute a safety check for that session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Cannot add checks to an aborted session"
**And** the session SHALL remain unchanged

#### Scenario: Cannot complete aborted session

**Given** a worker has a session with status "aborted"
**When** the worker attempts to complete the session
**Then** the request SHALL fail with HTTP 400
**And** the error message SHALL state "Cannot complete an aborted session"

---

### Requirement: Abort Session Authorization

Only the session owner SHALL be able to abort their sessions.

**Rationale:** Prevent unauthorized users from canceling worker sessions.

#### Scenario: Worker aborts their own session

**Given** a worker is authenticated as user ID "worker-123"
**And** a session exists owned by "worker-123"
**When** the worker aborts the session
**Then** the abort operation SHALL succeed
**And** the session SHALL be aborted

#### Scenario: Cannot abort another worker's session

**Given** a worker is authenticated as user ID "worker-123"
**And** a session exists owned by "worker-456"
**When** worker-123 attempts to abort the session
**Then** the request SHALL fail with HTTP 403
**And** the error message SHALL state "Not authorized to modify this session"
**And** the session SHALL remain unchanged

#### Scenario: Supervisor can abort any session

**Given** a supervisor is authenticated
**And** a worker has an in-progress session
**When** the supervisor aborts the session with reason "Safety protocol violation"
**Then** the abort operation SHALL succeed
**And** the session SHALL be aborted
**And** the abort_reason SHALL be recorded

---

### Requirement: Exclude Aborted Sessions from Default Lists

Aborted sessions SHALL be excluded from default session listings.

**Rationale:** Workers don't need to see aborted sessions in their regular workflow, but supervisors need access for auditing.

#### Scenario: Default session list excludes aborted

**Given** a worker has 2 sessions with status "in_progress"
**And** the worker has 1 session with status "aborted"
**And** the worker has 1 session with status "completed"
**When** the worker requests GET /api/v1/sessions
**Then** only 3 sessions SHALL be returned (in_progress and completed)
**And** the aborted session SHALL NOT be included

#### Scenario: Explicitly query for aborted sessions

**Given** a worker has 1 session with status "aborted"
**And** the worker has 3 sessions with other statuses
**When** the worker requests GET /api/v1/sessions?status=aborted
**Then** only the 1 aborted session SHALL be returned
**And** the abort_reason SHALL be included in the response

#### Scenario: Include all statuses including aborted

**Given** a worker has sessions with various statuses including "aborted"
**When** the worker requests GET /api/v1/sessions?include_aborted=true
**Then** all sessions including aborted SHALL be returned
**And** each session's status SHALL be clearly indicated

---

### Requirement: Audit Trail for Aborted Sessions

All aborted sessions SHALL be retained for audit purposes.

**Rationale:** Regulatory compliance requires maintaining records of all safety activities, including cancelled sessions.

#### Scenario: Supervisor views aborted session audit trail

**Given** a supervisor is authenticated
**And** a worker aborted a session with 5 completed checks
**When** the supervisor views the aborted session details
**Then** all 5 safety checks SHALL be visible
**And** the aborted_at timestamp SHALL be displayed
**And** the abort_reason SHALL be displayed if provided
**And** the worker_id SHALL be visible

#### Scenario: Aborted sessions appear in audit reports

**Given** a supervisor requests an audit report for date range
**And** 3 sessions were aborted in that date range
**When** the audit report is generated
**Then** the 3 aborted sessions SHALL be included
**And** abort reasons SHALL be included
**And** sessions SHALL be marked as "aborted" in the report

---

### Requirement: Domain Entity Abort Method

The WorkSession entity SHALL have an abort() method.

**Rationale:** Encapsulate abort logic in the domain entity following DDD principles.

#### Scenario: Entity abort method validates state

**Given** a WorkSession entity with status "in_progress"
**When** the abort(reason="Equipment failure") method is called
**Then** the status SHALL change to "aborted"
**And** the abort_reason SHALL be "Equipment failure"
**And** the locked flag SHALL remain false
**And** all checks SHALL be retained

#### Scenario: Entity prevents aborting locked sessions

**Given** a WorkSession entity with locked = true
**When** the abort() method is called
**Then** a ValueError SHALL be raised
**And** the error message SHALL state "Cannot modify a locked session"
**And** the status SHALL remain unchanged

#### Scenario: Entity prevents aborting completed sessions

**Given** a WorkSession entity with status "completed"
**When** the abort() method is called
**Then** a ValueError SHALL be raised
**And** the error message SHALL state "Cannot abort a completed session"
