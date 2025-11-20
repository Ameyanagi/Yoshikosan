# Audit Logging Spec

## ADDED Requirements

### Requirement: Supervisor Session Review
**ID**: audit-001
**Priority**: High
**Category**: Compliance

The system SHALL allow supervisors to review completed work sessions.

#### Scenario: List pending approval sessions
**Given** a user has supervisor role
**When** they request pending approvals
**Then** all completed but not approved sessions are returned
**And** sessions are ordered by completion time
**And** basic worker and SOP info is included

**Implementation**:
- Endpoint: `GET /api/v1/audit/sessions?status=pending`
- Authorization: Supervisor role required
- Query: `status=COMPLETED AND approved_at IS NULL`
- Response: List with pagination

---

### Requirement: Session Approval Workflow
**ID**: audit-002
**Priority**: High
**Category**: Compliance

The system SHALL allow supervisors to approve or reject completed sessions.

#### Scenario: Approve completed session
**Given** a supervisor is reviewing a completed session
**And** all checks appear valid
**When** they approve the session
**Then** the session status changes to "approved"
**And** the approval timestamp is recorded
**And** the supervisor ID is saved
**And** the session is locked (immutable)

**Implementation**:
- Endpoint: `POST /api/v1/audit/sessions/{id}/approve`
- Use case: `src/application/audit/approve_session.py`
- Domain method: `WorkSession.approve(supervisor_id)`
- Set `status=APPROVED`, `approved_at=NOW()`, `approved_by=supervisor_id`, `locked=true`

---

#### Scenario: Reject completed session
**Given** a supervisor finds issues in a session
**When** they reject the session with a reason
**Then** the session status changes to "rejected"
**And** the rejection reason is recorded
**And** the worker is notified
**And** the session remains locked but marked as invalid

**Implementation**:
- Endpoint: `POST /api/v1/audit/sessions/{id}/reject`
- Request: `{reason: str}`
- Add `rejection_reason` field to `work_sessions`
- Add `REJECTED` status to enum

---

### Requirement: Detailed Audit Trail View
**ID**: audit-003
**Priority**: High
**Category**: Compliance

The system SHALL provide detailed audit trail for each session.

#### Scenario: View session audit details
**Given** a supervisor is reviewing a session
**When** they request the full audit trail
**Then** all steps and checks are returned in chronological order
**And** each check includes result, feedback, timestamp
**And** any overrides are clearly marked
**And** the data is formatted for easy review

**Implementation**:
- Endpoint: `GET /api/v1/audit/sessions/{id}`
- Response includes:
  - Session metadata (worker, start/end times)
  - SOP details (title, tasks, steps)
  - All safety checks with timestamps and results
  - Confidence scores for each check
  - Override history
  - Timeline view data
- No image/audio evidence in MVP

---

### Requirement: Evidence Storage (Future Enhancement)
**ID**: audit-004
**Priority**: Low
**Category**: Future Enhancement

The system SHALL support storing check evidence (images, audio) in future versions.

#### Scenario: Access check image evidence (future)
**Given** a supervisor is reviewing a specific check
**When** image storage is implemented
**Then** the image will be served from secure storage
**And** access will be logged
**And** the image will only be accessible to authorized users

**Implementation**:
- Out of scope for MVP
- Future: Images stored in `storage/evidence/{session_id}/{check_id}.jpg`
- Future: Audio transcripts stored with checks
- MVP: Only timestamps and pass/fail results are stored

---

### Requirement: Audit Log Immutability
**ID**: audit-005
**Priority**: Critical
**Category**: Compliance

The system SHALL ensure audit logs cannot be modified after approval.

#### Scenario: Prevent modification of approved session
**Given** a session is approved and locked
**When** any modification is attempted
**Then** the operation is rejected
**And** the attempted modification is logged

**Implementation**:
- Database constraint: `locked=true` prevents updates
- Domain entity: All mutation methods check `self.locked`
- Application layer: Verify lock status before operations
- Audit log: Record modification attempts

---

### Requirement: Audit Data Export
**ID**: audit-006
**Priority**: Medium
**Category**: Compliance

The system SHALL allow export of audit data for reporting.

#### Scenario: Export session data to JSON
**Given** a supervisor has reviewed a session
**When** they export the session data
**Then** a JSON file is generated with all session details
**And** the file includes evidence URLs
**And** the file is timestamped and signed

**Implementation**:
- Endpoint: `GET /api/v1/audit/sessions/{id}/export`
- Response: JSON download
- Include: Session, SOP, checks, evidence URLs
- Add export timestamp and supervisor ID

---

### Requirement: Audit Search and Filtering
**ID**: audit-007
**Priority**: Low
**Category**: User Experience

The system SHALL support searching and filtering audit logs.

#### Scenario: Filter sessions by date range
**Given** a supervisor is viewing audit logs
**When** they apply date range filters
**Then** only sessions within the range are returned
**And** the filters persist in the URL

**Implementation**:
- Query params: `from_date`, `to_date`, `worker_id`, `sop_id`, `status`
- Apply filters to database query
- Return filtered results with pagination
