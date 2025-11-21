# session-display Specification

## Purpose
Enhance session display by including SOP title information, making it easier for workers to identify which procedure each session represents.

## ADDED Requirements

### Requirement: Include SOP Title in Session Response

The system SHALL include the SOP title in work session API responses.

**Rationale:** Workers need to quickly identify which procedure a session represents without having to look up the SOP separately. This is especially important when managing multiple active sessions.

#### Scenario: Session list includes SOP titles

**Given** a worker has 3 active sessions
**And** session 1 is for SOP titled "安全バルブ点検手順" (Safety Valve Inspection Procedure)
**And** session 2 is for SOP titled "ポンプ起動手順" (Pump Startup Procedure)
**And** session 3 is for SOP titled "緊急停止手順" (Emergency Shutdown Procedure)
**When** the worker requests GET /api/v1/sessions
**Then** each session in the response SHALL include a sop_title field
**And** session 1 SHALL have sop_title "安全バルブ点検手順"
**And** session 2 SHALL have sop_title "ポンプ起動手順"
**And** session 3 SHALL have sop_title "緊急停止手順"

#### Scenario: Single session response includes SOP title

**Given** a session exists for SOP titled "配管清掃手順" (Pipe Cleaning Procedure)
**When** the worker requests GET /api/v1/sessions/{session_id}
**Then** the response SHALL include sop_title field
**And** sop_title SHALL be "配管清掃手順"
**And** the response SHALL still include sop_id for reference

#### Scenario: Current session includes SOP title

**Given** a worker has an active session for SOP titled "点検記録作成手順"
**When** the worker requests GET /api/v1/sessions/current
**Then** the response SHALL include sop_title field
**And** sop_title SHALL be "点検記録作成手順"

---

### Requirement: SOP Title in Session Schema

The WorkSessionSchema SHALL include a sop_title field.

**Rationale:** API response schemas must be updated to include the new field for consistent data structure.

#### Scenario: WorkSessionSchema has sop_title field

**Given** the WorkSessionSchema is defined
**When** examining the schema definition
**Then** a sop_title field SHALL exist
**And** the field type SHALL be string
**And** the field SHALL be required (not nullable)
**And** the field SHALL be populated from the related SOP entity

#### Scenario: Session mapper includes SOP title

**Given** a session entity with related SOP
**When** the session is mapped to WorkSessionSchema
**Then** the mapper SHALL fetch the SOP title
**And** the sop_title field SHALL be populated in the schema
**And** the mapping SHALL use an efficient query (join or eager loading)

---

### Requirement: Efficient SOP Title Retrieval

The system SHALL retrieve SOP titles efficiently to avoid N+1 query problems.

**Rationale:** When listing multiple sessions, fetching SOP titles should not result in separate database queries for each session.

#### Scenario: List sessions with efficient SOP title loading

**Given** a worker has 10 sessions
**When** the worker requests GET /api/v1/sessions
**Then** the system SHALL use a single join or eager loading query
**And** all 10 SOP titles SHALL be fetched in one database roundtrip
**And** the response time SHALL be < 200ms

#### Scenario: Session repository eager loads SOP

**Given** the session repository is querying sessions
**When** fetching sessions that will include SOP titles
**Then** the repository SHALL use SQLAlchemy joinedload or selectinload
**And** the SOP relationship SHALL be eagerly loaded
**And** no additional queries SHALL be made for SOP titles

---

### Requirement: Display SOP Title in Audit Sessions

Audit session listings SHALL include SOP titles for supervisor review.

**Rationale:** Supervisors need to quickly identify which procedures were executed when reviewing audit trails.

#### Scenario: Audit session list includes SOP titles

**Given** a supervisor is reviewing completed sessions
**And** 5 sessions exist for various SOPs
**When** the supervisor requests GET /api/v1/audit/sessions
**Then** each session in the response SHALL include sop_title
**And** sessions SHALL be sortable by sop_title
**And** the response SHALL allow filtering by SOP title

#### Scenario: Audit session detail includes SOP title

**Given** a supervisor is reviewing a specific session
**When** the supervisor requests GET /api/v1/audit/sessions/{session_id}
**Then** the response SHALL include sop_title field
**And** the SOP title SHALL match the SOP associated with the session
