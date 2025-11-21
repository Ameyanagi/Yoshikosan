# Enable Session Management

## Overview
Enable workers to manage multiple work sessions by pausing active sessions and aborting unwanted sessions. This allows workers performing multiple jobs to switch between different SOPs without being restricted to a single active session.

## Motivation
Currently, workers are limited to one active session at a time. In real-world scenarios, workers often need to:
- Switch between different procedures when priorities change
- Handle emergency interruptions that require executing a different SOP
- Manage multiple concurrent work assignments

The current implementation blocks starting a new session if one is already active, forcing workers to complete their current SOP before starting another.

## Goals
1. Remove the single active session restriction
2. Allow workers to pause in-progress sessions and resume them later
3. Provide ability to abort/cancel unwanted sessions permanently
4. Display SOP title in session data for better visibility

## Non-Goals
- True concurrent execution of multiple SOPs (workers still work on one at a time, but can switch)
- Session priority management
- Automatic session timeout or cleanup
- Session sharing between workers

## Proposal

### Multiple Active Sessions
- Remove the constraint that prevents starting a new session when another is active
- Workers can have multiple sessions in `IN_PROGRESS` status simultaneously
- Workers work on one session at a time but can switch between them

### Pause Session
- Add `PAUSED` status to `SessionStatus` enum
- Add `pause_session` endpoint: `POST /api/v1/sessions/{session_id}/pause`
- Paused sessions:
  - Retain all safety checks and progress
  - Can be resumed to `IN_PROGRESS` status
  - Are included in worker's session list
  - Cannot have new checks added while paused

### Abort Session
- Add `ABORTED` status to `SessionStatus` enum
- Add `abort_session` endpoint: `POST /api/v1/sessions/{session_id}/abort`
- Aborted sessions:
  - Are soft-deleted (marked as aborted, not physically deleted)
  - Retain safety checks for audit purposes
  - Cannot be resumed
  - Are excluded from active session lists (unless explicitly queried)

### SOP Title in Session
- Include `sop_title` field in `WorkSessionSchema` response
- Populate from related SOP entity for better UX

## Impact Analysis

### Breaking Changes
None - this is purely additive functionality.

### Affected Components
- **Domain Layer**: `WorkSession` entity (new statuses, pause/abort methods)
- **Application Layer**: New use cases for pause/abort operations
- **API Layer**: New endpoints for pause/abort
- **Repository Layer**: Update queries to handle new statuses
- **Database**: Migration to add new status values

### Security Considerations
- Only the session owner can pause/abort their own sessions
- Supervisors should be able to view aborted sessions for audit

### Performance Considerations
- No significant performance impact
- May need index on (worker_id, status) for efficient querying

## Alternatives Considered

### Alternative 1: True Concurrent Execution
Allow workers to actively execute multiple SOPs simultaneously.
**Rejected**: Too complex for MVP, unclear UX for workers performing physical tasks.

### Alternative 2: Hard Delete Aborted Sessions
Physically delete aborted sessions from database.
**Rejected**: Loses audit trail, violates regulatory requirements for safety logging.

### Alternative 3: Session Queue System
Implement a priority queue for sessions.
**Rejected**: Over-engineered for current requirements, can be added later if needed.

## Dependencies
- Requires database migration for new session statuses
- Frontend needs UI updates to show multiple active sessions
- Frontend needs pause/abort buttons in session interface

## Success Criteria
1. Workers can start a new session while having other sessions in progress
2. Workers can pause a session and resume it later with all progress intact
3. Workers can abort unwanted sessions
4. SOP title is visible in session lists and detail views
5. All safety checks are retained in audit trail for paused/aborted sessions

## Related Specs
- `automation` spec (session management)
- `testing` spec (new test coverage requirements)
