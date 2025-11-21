# SOP Upload UI Spec

## ADDED Requirements

### Requirement: File Upload Interface
**ID**: sop-ui-001
**Priority**: High
**Category**: Frontend

The system SHALL provide a user interface for uploading SOP documents.

#### Scenario: Upload SOP files
**Given** a user is on the SOP upload page
**When** they select files (images or text)
**And** optionally enter text description
**And** click "Upload and Structure"
**Then** the files are validated client-side
**And** images are converted to base64 in memory (no file upload)
**And** a progress indicator is shown
**And** the data is sent to the backend as JSON
**And** the user is navigated to the review page

**Implementation**:
- Component: `app/(auth)/sop/upload/page.tsx`
- Form library: React Hook Form + Zod validation
- File input: Accept `.jpg, .jpeg, .png`
- Max size: 10MB per file
- **Base64 encoding**: Use `FileReader.readAsDataURL()` to convert images in browser
- API call: `POST /api/v1/sops` with JSON body:
  ```json
  {
    "title": "string",
    "images_base64": ["data:image/jpeg;base64,..."],
    "text_content": "string (optional)"
  }
  ```
- **No multipart/form-data**: All data sent as JSON with base64-encoded images

---

### Requirement: SOP Structuring Progress
**ID**: sop-ui-002
**Priority**: Medium
**Category**: User Experience

The system SHALL show progress while AI structures the SOP.

#### Scenario: Display structuring progress
**Given** SOP files have been uploaded
**When** the AI is processing the files
**Then** a loading spinner is displayed
**And** status messages update ("Analyzing images...", "Extracting tasks...", "Identifying hazards...")
**And** the user cannot navigate away without confirmation

**Implementation**:
- Use React Query mutation with loading state
- Display: Spinner + status text
- Prevent navigation: `beforeunload` event handler
- Timeout: Show error if > 30 seconds

---

### Requirement: Task List Review Interface
**ID**: sop-ui-003
**Priority**: High
**Category**: Frontend

The system SHALL display AI-structured tasks for user review.

#### Scenario: Display structured SOP
**Given** the SOP has been structured by AI
**When** the review page loads
**Then** all tasks, steps, and hazards are displayed
**And** each item is editable inline
**And** the user can add or remove items
**And** validation errors are highlighted

**Implementation**:
- Component: `app/(auth)/sop/review/[id]/page.tsx`
- Display: Accordion list (tasks → steps → hazards)
- Editing: Inline forms with React Hook Form
- Validation: At least one task, all tasks have steps
- State: Local state for edits, save on confirm

---

### Requirement: SOP Editing Controls
**ID**: sop-ui-004
**Priority**: High
**Category**: Frontend

The system SHALL allow users to edit AI-generated SOP structure.

#### Scenario: Edit task details
**Given** a user is reviewing a structured SOP
**When** they click "Edit" on a task
**Then** the task title and description become editable
**And** changes are validated in real-time
**And** "Save" and "Cancel" buttons appear
**And** saving updates the local state

**Implementation**:
- Inline editing: Toggle between view and edit mode
- Validation: Required fields, character limits
- Auto-save: Debounced input (3 seconds)
- Or explicit save button

---

#### Scenario: Add or remove steps
**Given** a user is editing a task
**When** they click "Add Step"
**Then** a new empty step form appears
**And** they can enter step description and details
**When** they click "Remove Step"
**Then** a confirmation dialog appears
**And** the step is removed from the list

**Implementation**:
- Add button: Appends new step to array
- Remove button: Confirmation dialog → splice from array
- Reorder: Drag-and-drop (optional, nice-to-have)

---

### Requirement: SOP Confirmation Flow
**ID**: sop-ui-005
**Priority**: High
**Category**: User Experience

The system SHALL require user confirmation before saving SOP.

#### Scenario: Confirm and save SOP
**Given** a user has reviewed and edited the SOP
**When** they click "Confirm and Start"
**Then** validation is performed
**And** if valid, the SOP is saved to the database
**And** the user is redirected to start a work session
**And** if invalid, errors are displayed

**Implementation**:
- Button: "Confirm and Start" (primary CTA)
- Validation: Call `sop.validate()` client-side + server-side
- API call: `PUT /api/v1/sops/{id}`
- Success: Navigate to `/session/start?sop_id={id}`
- Error: Display validation errors inline

---

### Requirement: SOP List View
**ID**: sop-ui-006
**Priority**: Medium
**Category**: Frontend

The system SHALL display a list of user's saved SOPs.

#### Scenario: View saved SOPs
**Given** a user has created SOPs
**When** they navigate to the SOP list page
**Then** all their SOPs are displayed
**And** each shows title, created date, and status
**And** they can select an SOP to start a new session
**And** they can edit or delete SOPs

**Implementation**:
- Component: `app/(auth)/sop/list/page.tsx`
- API call: `GET /api/v1/sops`
- Display: Cards or table with SOP details
- Actions: "Start Session", "Edit", "Delete"
- Pagination: Load more / infinite scroll

---

### Requirement: Responsive Mobile Design
**ID**: sop-ui-007
**Priority**: Medium
**Category**: User Experience

The system SHALL be usable on mobile devices.

#### Scenario: Upload SOP on mobile
**Given** a user accesses the upload page on mobile
**When** they interact with the interface
**Then** the UI adapts to the small screen
**And** file selection uses native mobile picker
**And** all controls are touch-friendly (min 44x44px)
**And** the layout is single-column

**Implementation**:
- Tailwind responsive classes: `flex-col md:flex-row`
- Mobile-first design
- Touch targets: Minimum 44px tap areas
- Test on iOS Safari and Android Chrome
