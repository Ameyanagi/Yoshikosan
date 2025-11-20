# Audit Review UI Spec

## ADDED Requirements

### Requirement: Session List View
**ID**: audit-ui-001
**Priority**: High
**Category**: Frontend

The system SHALL display a list of sessions for supervisor review.

#### Scenario: View pending approvals
**Given** a supervisor is logged in
**When** they navigate to the audit page
**Then** all pending approval sessions are listed
**And** each session shows worker name, SOP title, completion time
**And** sessions are ordered by most recent first
**And** the list is paginated

**Implementation**:
- Component: `app/(auth)/audit/page.tsx`
- API call: `GET /api/v1/audit/sessions?status=pending`
- Display: Table or card list
- Columns: Worker, SOP, Completed At, Actions
- Pagination: 20 per page with "Load More"

---

### Requirement: Session Detail View
**ID**: audit-ui-002
**Priority**: High
**Category**: Frontend

The system SHALL display detailed audit trail for a session.

#### Scenario: View session audit trail
**Given** a supervisor selects a session
**When** the detail page loads
**Then** the session metadata is displayed
**And** all steps are listed in order
**And** each step shows check result (pass/fail/override)
**And** evidence links (image, audio) are provided
**And** the timeline is clearly visualized

**Implementation**:
- Component: `app/(auth)/audit/sessions/[id]/page.tsx`
- API call: `GET /api/v1/audit/sessions/{id}`
- Layout: Timeline view with step cards
- Each card: Step description, check result, timestamp, evidence buttons
- Visual: Green (pass), red (fail), yellow (override)

---

### Requirement: Evidence Viewer (Future Enhancement)
**ID**: audit-ui-003
**Priority**: Low
**Category**: Future Enhancement

The system SHALL support viewing check evidence in future versions.

#### Scenario: View check details
**Given** a supervisor is reviewing a specific check
**When** they view the check in the timeline
**Then** they see the timestamp, result, and feedback text
**And** they see confidence score if available
**And** override information is displayed if applicable

**Implementation**:
- Display: Check card with timestamp, result badge, feedback text
- No image/audio viewer in MVP
- Future: Add modal for image viewing
- Future: Add audio playback controls

---

### Requirement: Approval Controls
**ID**: audit-ui-004
**Priority**: High
**Category**: Frontend

The system SHALL provide UI controls for session approval/rejection.

#### Scenario: Approve session
**Given** a supervisor has reviewed all checks
**And** all checks are satisfactory
**When** they click "Approve Session"
**Then** a confirmation dialog appears
**And** they confirm the approval
**Then** the session status updates to "approved"
**And** the session is locked
**And** a success message is shown

**Implementation**:
- Button: "Approve Session" (green, primary)
- Confirmation: Dialog with "Are you sure?"
- API call: `POST /api/v1/audit/sessions/{id}/approve`
- Success: Toast notification + navigate to list

---

#### Scenario: Reject session
**Given** a supervisor finds issues
**When** they click "Reject Session"
**Then** a dialog appears requesting a rejection reason
**And** they enter the reason and confirm
**Then** the session status updates to "rejected"
**And** the worker is notified (future: email/notification)

**Implementation**:
- Button: "Reject Session" (red, secondary)
- Dialog: Text input for reason (required)
- API call: `POST /api/v1/audit/sessions/{id}/reject` with `{reason}`
- Success: Toast notification + navigate to list

---

### Requirement: Filter and Search
**ID**: audit-ui-005
**Priority**: Medium
**Category**: User Experience

The system SHALL allow filtering audit logs.

#### Scenario: Filter by status
**Given** a supervisor is viewing the audit list
**When** they select a status filter (pending/approved/rejected)
**Then** the list updates to show only matching sessions
**And** the URL updates with the filter parameter
**And** the filter persists on page reload

**Implementation**:
- Component: Tabs or dropdown filter
- Options: "Pending", "Approved", "Rejected", "All"
- URL param: `?status=pending`
- React Query: Refetch with new filter

---

#### Scenario: Search by worker or SOP
**Given** a supervisor is viewing the audit list
**When** they enter a search query
**Then** the list filters to matching workers or SOPs
**And** the search is debounced (wait 500ms)
**And** results update in real-time

**Implementation**:
- Component: Search input with icon
- Debounce: Use `useDebouncedValue` hook
- API param: `?search={query}`
- Search fields: Worker name, SOP title

---

### Requirement: Export Functionality
**ID**: audit-ui-006
**Priority**: Low
**Category**: User Experience

The system SHALL allow exporting session data.

#### Scenario: Export session to JSON
**Given** a supervisor is viewing a session
**When** they click "Export"
**Then** a JSON file is downloaded
**And** the file contains all session details
**And** the filename includes session ID and timestamp

**Implementation**:
- Button: "Export" in session detail header
- API call: `GET /api/v1/audit/sessions/{id}/export`
- Download: `saveAs(blob, filename)`
- Filename: `session-{id}-{timestamp}.json`

---

### Requirement: Responsive Audit UI
**ID**: audit-ui-007
**Priority**: Medium
**Category**: User Experience

The system SHALL provide a mobile-friendly audit interface.

#### Scenario: Review session on mobile
**Given** a supervisor accesses audit page on mobile
**When** they view the session list and details
**Then** the UI adapts to the small screen
**And** tables become scrollable cards
**And** modals are full-screen on mobile
**And** all actions are accessible

**Implementation**:
- Table: Convert to cards on mobile (`hidden md:table`)
- Modals: Use `fullScreen` prop on small screens
- Touch-friendly: Large buttons, adequate spacing
- Test on mobile browsers
