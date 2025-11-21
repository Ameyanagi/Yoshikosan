# multiple-sessions Specification

## Purpose
Enable workers to have multiple work sessions in progress simultaneously, allowing them to switch between different SOPs as job priorities change.

## ADDED Requirements

### Requirement: Remove Single Active Session Restriction

The system SHALL allow workers to start new sessions while other sessions are in progress.

**Rationale:** Workers in industrial settings often need to switch between different procedures when priorities change or emergencies arise. The current single-session restriction blocks legitimate workflow patterns.

#### Scenario: Start new session with existing active session

**Given** a worker has an active session for SOP A
**When** the worker starts a new session for SOP B
**Then** the new session SHALL be created successfully
**And** both sessions SHALL have status "in_progress"
**And** the worker SHALL have 2 active sessions
**And** the original session SHALL remain unchanged

#### Scenario: Start multiple sessions sequentially

**Given** a worker has no active sessions
**When** the worker starts session for SOP A
**And** the worker starts session for SOP B  
**And** the worker starts session for SOP C
**Then** all 3 sessions SHALL be created successfully
**And** all 3 sessions SHALL have status "in_progress"
**And** each session SHALL maintain independent progress

---

### Requirement: List Active Sessions

The system SHALL provide an endpoint to list all active sessions for a worker.

**Rationale:** Workers need to see all their in-progress sessions to choose which one to continue working on.

#### Scenario: List multiple in-progress sessions

**Given** a worker has 3 sessions with status "in_progress"
**And** the worker has 2 sessions with status "completed"
**When** the worker requests GET /api/v1/sessions
**Then** all 5 sessions SHALL be returned
**And** sessions SHALL be ordered by started_at descending (newest first)
**And** each session SHALL include SOP title for identification

#### Scenario: List sessions when none exist

**Given** a worker has no sessions
**When** the worker requests GET /api/v1/sessions
**Then** an empty array SHALL be returned
**And** the response status SHALL be 200 OK

---

### Requirement: Session Isolation

Each session SHALL maintain independent state and progress.

**Rationale:** Sessions for different SOPs must not interfere with each other to prevent safety hazards.

#### Scenario: Progress in one session doesn't affect others

**Given** a worker has session A on step 2 of 5
**And** the worker has session B on step 3 of 4
**When** the worker completes a check in session A and advances to step 3
**Then** session A SHALL be on step 3 of 5
**And** session B SHALL still be on step 3 of 4
**And** each session's check history SHALL be independent

#### Scenario: Complete one session while others remain active

**Given** a worker has 3 active sessions
**When** the worker completes all steps in session A
**Then** session A SHALL have status "completed"
**And** the other 2 sessions SHALL remain with status "in_progress"
**And** the worker can continue the other sessions

---

### Requirement: Database Query Optimization

The system SHALL efficiently query sessions by worker and status.

**Rationale:** With multiple sessions per worker, queries must remain performant.

#### Scenario: Index on worker_id and status

**Given** the database has a sessions table
**When** querying sessions by worker_id and status
**Then** the query SHALL use an index on (worker_id, status)
**And** the query SHALL complete in < 100ms for up to 100 sessions

#### Scenario: Filter sessions by status

**Given** a worker has sessions with various statuses
**When** querying for sessions with status "in_progress"
**Then** only sessions matching the status SHALL be returned
**And** the query SHALL use the composite index efficiently
