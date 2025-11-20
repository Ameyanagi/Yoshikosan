# Tasks: Implement SOP Workflow Application

## Phase 1: Database Foundation (Backend)

### 1.1 Database Schema - SOP Tables
- [ ] Create Alembic migration `001_create_sop_tables.py`
- [ ] Define `sops` table: id (UUID PK), title (TEXT), created_by (UUID FK→users), created_at, updated_at, deleted_at
- [ ] Define `tasks` table: id (UUID PK), sop_id (UUID FK→sops CASCADE), title (TEXT), description (TEXT), order_index (INTEGER), created_at
- [ ] Define `steps` table: id (UUID PK), task_id (UUID FK→tasks CASCADE), description (TEXT), order_index (INTEGER), expected_action (TEXT), expected_result (TEXT)
- [ ] Define `hazards` table: id (UUID PK), step_id (UUID FK→steps CASCADE), description (TEXT), severity (TEXT), mitigation (TEXT)
- [ ] Add indexes: `idx_sops_created_by`, `idx_tasks_sop_id`, `idx_steps_task_id`, `idx_hazards_step_id`
- [ ] Test migration: `alembic upgrade head` and verify tables created

**Validation**: Run `alembic upgrade head && psql -d yoshikosan_db -c "\dt"` and verify all 4 tables exist

---

### 1.2 Database Schema - Work Session Tables
- [ ] Create Alembic migration `002_create_session_tables.py`
- [ ] Define `work_sessions` table: id (UUID PK), sop_id (UUID FK→sops), worker_id (UUID FK→users), status (TEXT), current_step_id (UUID FK→steps nullable), started_at, completed_at, approved_at, approved_by (UUID FK→users nullable), locked (BOOLEAN default false), rejection_reason (TEXT nullable)
- [ ] Define `safety_checks` table: id (UUID PK), session_id (UUID FK→work_sessions), step_id (UUID FK→steps), result (TEXT), feedback_text (TEXT), confidence_score (FLOAT nullable), needs_review (BOOLEAN default false), checked_at, override_reason (TEXT nullable), override_by (UUID FK→users nullable)
- [ ] Add indexes: `idx_sessions_status`, `idx_sessions_worker_id`, `idx_sessions_sop_id`, `idx_checks_session_id`, `idx_checks_result`
- [ ] Add constraint: CHECK(status IN ('in_progress', 'completed', 'approved', 'rejected'))
- [ ] Add constraint: CHECK(result IN ('pass', 'fail', 'override'))
- [ ] Test migration and verify foreign keys work
- [ ] Note: No image_url, audio_url, or transcript fields in MVP

**Validation**: Insert test data and verify CASCADE behavior

---

### 1.3 SQLAlchemy ORM Models
- [ ] Create `src/infrastructure/database/models.py`
- [ ] Define `SOPModel` class with relationships to TaskModel
- [ ] Define `TaskModel` class with relationships to StepModel
- [ ] Define `StepModel` class with relationships to HazardModel
- [ ] Define `HazardModel` class
- [ ] Define `WorkSessionModel` class with relationships to SafetyCheckModel
- [ ] Define `SafetyCheckModel` class
- [ ] Use `Text` column type for all string fields
- [ ] Use `relationship()` with `lazy="selectin"` for async loading
- [ ] Add `__repr__` methods for debugging
- [ ] Test models with test database

**Validation**: Create test instances and verify relationships load correctly

---

## Phase 2: Domain Layer (Backend)

### 2.1 SOP Domain Entities
- [ ] Create `src/domain/sop/entities.py`
- [ ] Implement `Hazard` dataclass with fields: id, description, severity, mitigation
- [ ] Implement `Step` dataclass with fields: id, description, order_index, expected_action, expected_result, hazards list
- [ ] Add `Step.add_hazard(description, severity, mitigation)` method
- [ ] Implement `Task` dataclass with fields: id, title, description, order_index, steps list
- [ ] Add `Task.add_step(description, expected_action)` method
- [ ] Implement `SOP` dataclass (aggregate root) with fields: id, title, created_by, tasks list, created_at, updated_at, deleted_at
- [ ] Add `SOP.add_task(title, description)` method
- [ ] Implement `SOP.validate()` method returning list of errors
- [ ] Add business rule validations: title required, at least one task, tasks have steps
- [ ] Write unit tests for all domain methods

**Validation**: Run `pytest src/domain/sop/test_entities.py -v`

---

### 2.2 Work Session Domain Entities
- [ ] Create `src/domain/work_session/entities.py`
- [ ] Define `SessionStatus` enum: IN_PROGRESS, COMPLETED, APPROVED, REJECTED
- [ ] Define `CheckResult` enum: PASS, FAIL, OVERRIDE
- [ ] Implement `SafetyCheck` dataclass with all required fields
- [ ] Implement `WorkSession` dataclass (aggregate root)
- [ ] Add `WorkSession.add_check(step_id, result, feedback_text, image_url, ...)` method
- [ ] Add `WorkSession.advance_to_next_step(next_step_id)` method
- [ ] Add `WorkSession.complete()` method
- [ ] Add `WorkSession.approve(supervisor_id)` method
- [ ] Add `WorkSession.override_last_check(reason, supervisor_id)` method
- [ ] Add lock checks: raise ValueError if locked
- [ ] Write unit tests for session lifecycle

**Validation**: Run `pytest src/domain/work_session/test_entities.py -v`

---

### 2.3 SOP Repository
- [ ] Create `src/domain/sop/repositories.py` with `SOPRepository` Protocol
- [ ] Define methods: `save(sop)`, `get_by_id(id)`, `list_by_user(user_id)`, `delete(id)`
- [ ] Create `src/infrastructure/database/repositories/sop_repository.py`
- [ ] Implement `SQLAlchemySOPRepository` class
- [ ] Create `src/infrastructure/database/mappers/sop_mapper.py`
- [ ] Implement `to_domain(model: SOPModel) -> SOP` mapper
- [ ] Implement `to_model(entity: SOP) -> SOPModel` mapper
- [ ] Handle recursive mapping of tasks → steps → hazards
- [ ] Use eager loading: `joinedload(SOPModel.tasks).joinedload(TaskModel.steps).joinedload(StepModel.hazards)`
- [ ] Write integration tests with test database

**Validation**: Run `pytest tests/integration/test_sop_repository.py -v`

---

### 2.4 Work Session Repository
- [ ] Create `src/domain/work_session/repositories.py` with `WorkSessionRepository` Protocol
- [ ] Define methods: `save(session)`, `get_by_id(id)`, `get_current_for_worker(worker_id)`, `list_by_worker(worker_id)`
- [ ] Create `src/infrastructure/database/repositories/session_repository.py`
- [ ] Implement `SQLAlchemyWorkSessionRepository` class
- [ ] Create `src/infrastructure/database/mappers/session_mapper.py`
- [ ] Implement mappers for WorkSession ↔ WorkSessionModel
- [ ] Handle SafetyCheck list mapping
- [ ] Use eager loading for checks
- [ ] Write integration tests

**Validation**: Run `pytest tests/integration/test_session_repository.py -v`

---

## Phase 3: Application Layer (Backend)

### 3.1 SOP Upload Use Case
- [ ] Create `src/application/sop/upload_sop.py`
- [ ] Implement `UploadSOPUseCase` class
- [ ] Accept file uploads (images) and optional text input
- [ ] Save uploaded image files to `storage/sops/{sop_id}/`
- [ ] Save text input to SOP record
- [ ] Create initial SOP entity with pending status
- [ ] Call SOPRepository.save()
- [ ] Return SOP ID for structuring step
- [ ] Handle file validation errors (file size, format)
- [ ] Write unit tests with mocked repository

**Validation**: Run `pytest tests/unit/application/sop/test_upload_sop.py -v`

---

### 3.2 SOP Structuring Use Case
- [ ] Create `src/application/sop/structure_sop.py`
- [ ] Implement `StructureSOPUseCase` class
- [ ] Define `STRUCTURE_SOP_PROMPT` template (see design.md)
- [ ] Include user-provided text in prompt if available
- [ ] Define JSON schema for SOP structure response
- [ ] Load SOP by ID with images and text
- [ ] Encode images to base64
- [ ] Call SambaNova `analyze_image()` with prompt, images, and response schema
- [ ] The vision model will extract text from images and combine with provided text
- [ ] Parse JSON response into SOP aggregate (tasks, steps, hazards)
- [ ] Update SOP status to "structured"
- [ ] Save updated SOP
- [ ] Handle AI errors gracefully (set status to "failed")
- [ ] Write unit tests with mocked AI service

**Validation**: Run integration test with real LEGO SOP images and text

---

### 3.3 Execute Safety Check Use Case
- [ ] Create `src/application/safety_check/execute_safety_check.py`
- [ ] Implement `ExecuteSafetyCheckUseCase` class
- [ ] Accept: session_id, step_id, image_base64, audio_base64
- [ ] Load work session and verify not locked
- [ ] Load complete SOP with all tasks and steps for full workflow context
- [ ] Identify current expected step from session state
- [ ] Transcribe audio using SambaNova Whisper
- [ ] Define `VERIFY_SAFETY_CHECK_PROMPT` template (see design.md)
- [ ] Format entire SOP structure in prompt for full context
- [ ] Call SambaNova multimodal analysis with image + transcript + full SOP context
- [ ] Parse AI response: result, confidence, feedback_ja, reasoning, step_sequence_correct
- [ ] If worker appears to be on wrong step, include correction in feedback
- [ ] Generate voice feedback using Hume AI (return audio bytes directly)
- [ ] **Do NOT save images or audio to disk** (MVP simplification)
- [ ] Create SafetyCheck entity (without image/audio URLs)
- [ ] Add check to session
- [ ] If pass and sequence correct: determine next step and advance session
- [ ] Save session with new check (timestamp, result, feedback only)
- [ ] Return result with feedback, audio bytes, and next step
- [ ] Write unit tests with mocked services

**Validation**: Run integration test with real photo + audio

---

### 3.4 Start Session Use Case
- [ ] Create `src/application/work_session/start_session.py`
- [ ] Implement `StartSessionUseCase` class
- [ ] Accept: sop_id, worker_id
- [ ] Validate SOP exists and is structured
- [ ] Check for existing active session (error if found)
- [ ] Query SOP for first step ID
- [ ] Create WorkSession entity with IN_PROGRESS status
- [ ] Set current_step_id to first step
- [ ] Save session
- [ ] Return session with first step details
- [ ] Write unit tests

**Validation**: Run `pytest tests/unit/application/work_session/test_start_session.py -v`

---

### 3.5 Approve Session Use Case
- [ ] Create `src/application/audit/approve_session.py`
- [ ] Implement `ApproveSessionUseCase` class
- [ ] Accept: session_id, supervisor_id
- [ ] Load session
- [ ] Verify session status is COMPLETED
- [ ] Verify user is supervisor
- [ ] Call `session.approve(supervisor_id)`
- [ ] Save locked session
- [ ] Return success
- [ ] Write unit tests

**Validation**: Run `pytest tests/unit/application/audit/test_approve_session.py -v`

---

## Phase 4: API Layer (Backend)

### 4.1 SOP Endpoints
- [ ] Create `src/api/v1/endpoints/sop.py`
- [ ] Implement `POST /api/v1/sops` - upload and structure SOP
  - Accept multipart/form-data with files and text
  - Call UploadSOPUseCase then StructureSOPUseCase
  - Return structured SOP JSON
- [ ] Implement `GET /api/v1/sops` - list user's SOPs
  - Query params: limit, offset
  - Filter by current user
  - Exclude deleted (WHERE deleted_at IS NULL)
- [ ] Implement `GET /api/v1/sops/{id}` - get SOP details
  - Authorize: only owner can view
  - Return full SOP with tasks/steps/hazards
- [ ] Implement `PUT /api/v1/sops/{id}` - update SOP
  - Accept full SOP JSON
  - Validate structure
  - Save changes
- [ ] Implement `DELETE /api/v1/sops/{id}` - soft delete SOP
  - Check for active sessions
  - Set deleted_at timestamp
- [ ] Create Pydantic schemas in `src/schemas/sop.py`
- [ ] Add to router in `src/api/v1/api.py`
- [ ] Write API integration tests

**Validation**: Run `pytest tests/integration/api/test_sop_endpoints.py -v`

---

### 4.2 Work Session Endpoints
- [ ] Create `src/api/v1/endpoints/session.py`
- [ ] Implement `POST /api/v1/sessions` - start new session
  - Request: `{sop_id}`
  - Call StartSessionUseCase
  - Return session with first step
- [ ] Implement `GET /api/v1/sessions/current` - get active session
  - Query for IN_PROGRESS session for current user
  - Return session with checks and current step
- [ ] Implement `GET /api/v1/sessions` - list sessions
  - Query params: status, limit, offset
  - Return session list
- [ ] Implement `GET /api/v1/sessions/{id}` - get session details
  - Authorize: only owner or supervisor
  - Return full session
- [ ] Implement `POST /api/v1/sessions/{id}/complete` - complete session
  - Call WorkSession.complete()
  - Save and return
- [ ] Create Pydantic schemas in `src/schemas/session.py`
- [ ] Add to router
- [ ] Write API integration tests

**Validation**: Run `pytest tests/integration/api/test_session_endpoints.py -v`

---

### 4.3 Safety Check Endpoints
- [ ] Create `src/api/v1/endpoints/check.py`
- [ ] Implement `POST /api/v1/checks` - execute safety check
  - Request: `{session_id, step_id, image_base64, audio_base64}`
  - Validate base64 data
  - Call ExecuteSafetyCheckUseCase
  - Return check result with feedback text and audio bytes (base64)
  - Timeout: 10 seconds
  - **Do NOT store images/audio files**
- [ ] Implement `GET /api/v1/checks/{id}` - get check details
  - Return check with timestamp, result, feedback, confidence
  - No evidence URLs in MVP
- [ ] Implement `POST /api/v1/checks/{id}/override` - manual override
  - Authorize: supervisor only
  - Request: `{result, reason}`
  - Update check result
  - Save and return
- [ ] Create Pydantic schemas in `src/schemas/check.py`
- [ ] Add to router
- [ ] Write API integration tests

**Validation**: Run integration test with real image/audio upload

---

### 4.4 Audit Endpoints
- [ ] Create `src/api/v1/endpoints/audit.py`
- [ ] Implement `GET /api/v1/audit/sessions` - list sessions for review
  - Authorize: supervisor only
  - Query params: status (default pending), limit, offset
  - Return session list with worker info
- [ ] Implement `GET /api/v1/audit/sessions/{id}` - get audit trail
  - Authorize: supervisor only
  - Return full session with all checks and evidence
- [ ] Implement `POST /api/v1/audit/sessions/{id}/approve` - approve session
  - Authorize: supervisor only
  - Call ApproveSessionUseCase
  - Return success
- [ ] Implement `POST /api/v1/audit/sessions/{id}/reject` - reject session
  - Authorize: supervisor only
  - Request: `{reason}`
  - Update session status and reason
  - Return success
- [ ] Implement `GET /api/v1/audit/sessions/{id}/export` - export to JSON
  - Return JSON download
- [ ] Create Pydantic schemas in `src/schemas/audit.py`
- [ ] Add to router
- [ ] Write API integration tests

**Validation**: Run `pytest tests/integration/api/test_audit_endpoints.py -v`

---

### 4.5 Static File Serving (Future)
- [ ] ~~Static file serving not needed for MVP~~
- [ ] ~~No evidence storage in MVP~~
- [ ] Future: Add `/media/` endpoint for stored evidence
- [ ] Future: Add authorization checks

**Validation**: N/A for MVP

---

## Phase 5: Frontend Dependencies

### 5.1 Install Frontend Packages
- [ ] Navigate to `yoshikosan-frontend/`
- [ ] Install: `bun add @tanstack/react-query`
- [ ] Install: `bun add zustand`
- [ ] Install: `bun add react-hook-form zod @hookform/resolvers`
- [ ] Verify `package.json` updated
- [ ] Run `bun install` to ensure lockfile is correct

**Validation**: Run `bun run build` and verify no errors

---

## Phase 6: Frontend Core Infrastructure

### 6.1 API Client Setup
- [ ] Create `lib/api/client.ts`
- [ ] Implement base API client with fetch wrapper
- [ ] Add auth token injection from session
- [ ] Add error handling and response parsing
- [ ] Create `lib/api/types.ts` matching backend schemas
- [ ] Define TypeScript interfaces for SOP, Task, Step, Hazard, WorkSession, SafetyCheck

**Validation**: Test API client with existing auth endpoints

---

### 6.2 React Query Configuration
- [ ] Create `lib/query/query-client.ts`
- [ ] Configure QueryClient with default options
- [ ] Set staleTime: 5 minutes
- [ ] Set cacheTime: 10 minutes
- [ ] Create `lib/query/keys.ts` with query key factory
- [ ] Update `app/layout.tsx` to wrap with QueryClientProvider
- [ ] Add React Query DevTools (dev only)

**Validation**: Verify React Query DevTools appear in browser

---

### 6.3 Zustand Session Store
- [ ] Create `lib/stores/session-store.ts`
- [ ] Define `SessionState` interface
- [ ] Implement store with: sessionId, currentStepIndex, isRecording, lastFeedback
- [ ] Add actions: startSession, advanceStep, setRecording, setFeedback, reset
- [ ] Use `create` from zustand
- [ ] Add persist middleware (optional)

**Validation**: Import and test store in a test component

---

### 6.4 API Hooks
- [ ] Create `lib/hooks/use-sops.ts`
  - `useSOPs()` - list user SOPs
  - `useSOP(id)` - get SOP details
  - `useUploadSOP()` - mutation for upload
  - `useUpdateSOP(id)` - mutation for updates
  - `useDeleteSOP(id)` - mutation for delete
- [ ] Create `lib/hooks/use-sessions.ts`
  - `useCurrentSession()` - get active session
  - `useSessions()` - list sessions
  - `useSession(id)` - get session details
  - `useStartSession()` - mutation to start
  - `useCompleteSession(id)` - mutation to complete
- [ ] Create `lib/hooks/use-checks.ts`
  - `useExecuteCheck()` - mutation for check submission
  - `useOverrideCheck(id)` - mutation for override
- [ ] Create `lib/hooks/use-audit.ts`
  - `useAuditSessions()` - list for supervisor
  - `useAuditSession(id)` - get audit trail
  - `useApproveSession(id)` - mutation to approve
  - `useRejectSession(id)` - mutation to reject

**Validation**: Test hooks in isolation with mock API

---

## Phase 7: Frontend UI - Phase 1 (SOP Upload)

### 7.1 SOP Upload Page
- [ ] Create `app/(auth)/sop/upload/page.tsx`
- [ ] Implement file upload form with React Hook Form
- [ ] Add file input for images/text (accept: .txt, .jpg, .jpeg, .png)
- [ ] Add optional text area for manual SOP input
- [ ] Add Zod validation: max file size 10MB
- [ ] Show file previews for selected files
- [ ] Implement submit handler calling `useUploadSOP()` hook
- [ ] Show loading spinner during upload and structuring
- [ ] Display progress messages ("Analyzing...", "Extracting tasks...")
- [ ] On success, navigate to `/sop/review/{id}`
- [ ] On error, display error toast

**Validation**: Upload test SOP and verify navigation to review page

---

### 7.2 SOP Review Page
- [ ] Create `app/(auth)/sop/review/[id]/page.tsx`
- [ ] Fetch SOP details using `useSOP(id)` hook
- [ ] Display SOP title (editable)
- [ ] Render tasks in accordion component
- [ ] Each task shows: title, description, steps list
- [ ] Each step shows: description, expected action/result, hazards
- [ ] Implement inline editing for all fields
- [ ] Add "Add Task", "Add Step", "Add Hazard" buttons
- [ ] Add "Remove" buttons with confirmation dialogs
- [ ] Validate: at least one task, all tasks have steps
- [ ] Add "Save Changes" button (calls `useUpdateSOP()`)
- [ ] Add "Confirm and Start Session" button
- [ ] On confirm, navigate to `/session/start?sop_id={id}`

**Validation**: Edit SOP and verify changes persist, start session

---

### 7.3 SOP List Page
- [ ] Create `app/(auth)/sop/list/page.tsx`
- [ ] Fetch SOPs using `useSOPs()` hook
- [ ] Display as cards or table
- [ ] Show: title, created date, status
- [ ] Add "Start Session" button (navigate to `/session/start?sop_id={id}`)
- [ ] Add "Edit" button (navigate to `/sop/review/{id}`)
- [ ] Add "Delete" button with confirmation (calls `useDeleteSOP()`)
- [ ] Implement pagination (20 per page)
- [ ] Add "Upload New SOP" button (navigate to `/sop/upload`)
- [ ] Show empty state if no SOPs

**Validation**: Verify all CRUD operations work

---

## Phase 8: Frontend UI - Phase 2 (Work Execution)

### 8.1 Session Start Page
- [ ] Create `app/(auth)/session/start/page.tsx`
- [ ] Get `sop_id` from query params
- [ ] Call `useStartSession()` mutation
- [ ] Initialize session store with session ID
- [ ] On success, navigate to `/session/execute/{session_id}`
- [ ] Show loading state
- [ ] Handle error: active session already exists

**Validation**: Start session and verify redirect

---

### 8.2 Work Execution Page - Camera Setup
- [ ] Create `app/(auth)/session/execute/[id]/page.tsx`
- [ ] Request camera permission: `navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}})`
- [ ] Display live camera feed in `<video autoplay />` element
- [ ] Layout: Top half camera, bottom half task info
- [ ] Handle camera permission denied gracefully
- [ ] Add fallback: manual image upload if camera fails

**Validation**: Verify camera preview works on desktop and mobile

---

### 8.3 Work Execution Page - Current Step Display
- [ ] Fetch session details using `useSession(id)` hook
- [ ] Display current step description
- [ ] Display expected action and result
- [ ] Show hazards with warning icons
- [ ] Display step progress: "Step 3 of 12"
- [ ] Add progress bar showing completion percentage
- [ ] Show completed steps with checkmarks

**Validation**: Verify step info updates as session progresses

---

### 8.4 Work Execution Page - "ヨシッ!" Button
- [ ] Add prominent "ヨシッ!" button (large, green)
- [ ] On click:
  1. Capture photo from video stream using `<canvas>`
  2. Convert canvas to base64 JPEG
  3. Start audio recording
- [ ] Disable button during processing
- [ ] Show captured image thumbnail briefly

**Validation**: Click button and verify photo captured

---

### 8.5 Work Execution Page - Audio Recording
- [ ] Request microphone permission: `getUserMedia({audio: true})`
- [ ] Start MediaRecorder on button click
- [ ] Record for max 10 seconds (auto-stop)
- [ ] Show recording indicator and timer
- [ ] Allow manual stop with button
- [ ] Convert audio Blob to base64
- [ ] Submit photo + audio to backend

**Validation**: Record audio and verify base64 output

---

### 8.6 Work Execution Page - Check Submission
- [ ] Call `useExecuteCheck()` mutation with captured data
- [ ] Show loading spinner: "Analyzing your check..."
- [ ] Implement 10-second timeout
- [ ] On success: Display feedback (text + audio)
- [ ] On failure: Display error toast with retry button

**Validation**: Submit check and verify API call

---

### 8.7 Work Execution Page - Feedback Display
- [ ] Parse check result (pass/fail/override)
- [ ] Show success icon (green checkmark) for pass
- [ ] Show warning icon (red X) for fail
- [ ] Display feedback text in Japanese
- [ ] Decode audio bytes from API response
- [ ] Play feedback audio automatically using `<audio autoplay />` with blob URL
- [ ] If pass: Highlight next step and scroll into view
- [ ] If fail: Show "Retry" button and "Manual Override" button (supervisor only)
- [ ] Update session store with new step index (if pass)
- [ ] Re-enable "ヨシッ!" button after feedback
- [ ] **Do NOT persist audio** - play once and discard

**Validation**: Verify feedback appears and audio plays

---

### 8.8 Work Execution Page - Session Completion
- [ ] Detect when last step is completed (next_step === null)
- [ ] Show completion celebration (confetti or success animation)
- [ ] Display "Session Complete!" message
- [ ] Add "Mark Complete" button
- [ ] On click: Call `useCompleteSession()` mutation
- [ ] Navigate to `/audit/sessions/{id}` for review

**Validation**: Complete full session and verify redirect

---

### 8.9 Work Execution Page - Manual Override
- [ ] Show "Manual Override" button only for supervisors
- [ ] On click: Open modal with reason input
- [ ] Call `useOverrideCheck(checkId)` mutation with reason
- [ ] Update UI to show override status
- [ ] Advance to next step on successful override

**Validation**: Override failed check and verify progression

---

## Phase 9: Frontend UI - Phase 3 (Audit Review)

### 9.1 Audit List Page
- [ ] Create `app/(auth)/audit/page.tsx`
- [ ] Authorize: Supervisor role required
- [ ] Fetch sessions using `useAuditSessions({status: 'pending'})`
- [ ] Display as table with columns: Worker, SOP, Completed At, Actions
- [ ] Add filter tabs: Pending, Approved, Rejected, All
- [ ] Add search input (debounced 500ms)
- [ ] Implement pagination (20 per page)
- [ ] Add "View Details" button for each session
- [ ] Navigate to `/audit/sessions/{id}` on click

**Validation**: Verify list loads and filters work

---

### 9.2 Audit Detail Page
- [ ] Create `app/(auth)/audit/sessions/[id]/page.tsx`
- [ ] Fetch session details using `useAuditSession(id)`
- [ ] Display session metadata: Worker, SOP, timestamps
- [ ] Render timeline view of all steps and checks
- [ ] Each check shows: Step description, result (pass/fail/override), timestamp
- [ ] Add image thumbnail for each check
- [ ] Add audio playback button for each check
- [ ] Highlight failed checks in red
- [ ] Highlight overrides in yellow
- [ ] Show override reasons if present

**Validation**: Verify timeline displays correctly

---

### 9.3 Check Details Display
- [ ] Display check cards in timeline
- [ ] Each card shows: timestamp, result badge (pass/fail/override), feedback text
- [ ] Show confidence score if available
- [ ] Highlight failed checks in red
- [ ] Highlight overrides in yellow with reason
- [ ] Show override details (who, when, why)
- [ ] **No image/audio viewer in MVP**
- [ ] Future: Add evidence modal when storage is implemented

**Validation**: Verify all check data displays correctly

---

### 9.4 Approval Controls
- [ ] Add "Approve Session" button (green, primary)
- [ ] Add "Reject Session" button (red, secondary)
- [ ] Only show if session status is "completed"
- [ ] On "Approve" click: Show confirmation dialog
- [ ] On confirm: Call `useApproveSession(id)` mutation
- [ ] On "Reject" click: Show dialog with reason input (required)
- [ ] On confirm: Call `useRejectSession(id)` mutation with reason
- [ ] Display success toast on successful action
- [ ] Navigate back to `/audit` list

**Validation**: Approve and reject sessions

---

### 9.5 Export Functionality
- [ ] Add "Export" button in audit detail header
- [ ] On click: Download JSON file via `/api/v1/audit/sessions/{id}/export`
- [ ] Filename: `session-{id}-{timestamp}.json`
- [ ] Use `saveAs` or anchor download

**Validation**: Export session and verify JSON contents

---

## Phase 10: Testing and Quality

### 10.1 Backend Unit Tests
- [ ] Write tests for all domain entities (SOP, WorkSession)
- [ ] Write tests for all use cases (mocked dependencies)
- [ ] Target: >80% coverage for domain and application layers
- [ ] Run: `make test-backend`

**Validation**: Coverage report shows >80%

---

### 10.2 Backend Integration Tests
- [ ] Write tests for all API endpoints
- [ ] Use httpx AsyncClient with test database
- [ ] Test happy paths and error cases
- [ ] Test authorization (owner-only, supervisor-only)
- [ ] Run: `make test-backend`

**Validation**: All API tests pass

---

### 10.3 Manual E2E Testing
- [ ] Test full Phase 1 flow: Upload → Review → Confirm
- [ ] Test full Phase 2 flow: Start → Execute all steps → Complete
- [ ] Test full Phase 3 flow: Review → Approve
- [ ] Test on mobile browsers (iOS Safari, Android Chrome)
- [ ] Test camera and microphone permissions
- [ ] Test error scenarios (network failures, AI timeouts)

**Validation**: All critical paths work end-to-end

---

### 10.4 Performance Testing
- [ ] Measure AI response times (target <3s for checks)
- [ ] Test with 10 concurrent users
- [ ] Verify database queries are optimized (no N+1)
- [ ] Check image/audio file sizes (compress if needed)

**Validation**: All performance targets met

---

## Phase 11: Deployment and Documentation

### 11.1 Database Migration in Production
- [ ] Backup production database
- [ ] Run `alembic upgrade head` in production
- [ ] Verify tables created correctly
- [ ] Test rollback: `alembic downgrade -1` then upgrade again

**Validation**: Production database schema matches dev

---

### 11.2 Environment Configuration
- [ ] Update `.env` with production values
- [ ] Verify all API keys are set (SambaNova, Hume AI)
- [ ] Set `ALLOWED_ORIGINS` to HTTPS domain
- [ ] Configure database connection pool size

**Validation**: Backend starts without errors

---

### 11.3 Docker Deployment
- [ ] Build Docker images: `make docker-build`
- [ ] Start containers: `make docker-up`
- [ ] Verify frontend accessible at https://yoshikosan.ameyanagi.com
- [ ] Verify backend API at https://yoshikosan.ameyanagi.com/api
- [ ] Test file uploads and static file serving

**Validation**: All services running and accessible

---

### 11.4 Monitoring and Logging
- [ ] Configure backend logging (production level: INFO)
- [ ] Set up error tracking (Sentry or similar, optional)
- [ ] Monitor AI service latency
- [ ] Set up database connection monitoring

**Validation**: Logs visible via `make docker-logs`

---

### 11.5 Documentation
- [ ] Update README with usage instructions
- [ ] Document API endpoints (auto-generated via FastAPI /docs)
- [ ] Create user guide for workers (how to use Phase 1 and 2)
- [ ] Create supervisor guide (how to use Phase 3)
- [ ] Document deployment process

**Validation**: Docs are clear and complete

---

## Dependencies
- All existing infrastructure (AI services, auth, deployment) must be working
- Requires SambaNova and Hume AI API keys
- Requires test data: LEGO SOP images and text

## Estimated Time
- Phase 1 (DB): 4 hours
- Phase 2 (Domain): 6 hours
- Phase 3 (Application): 8 hours
- Phase 4 (API): 6 hours
- Phase 5-6 (Frontend Core): 4 hours
- Phase 7 (SOP UI): 6 hours
- Phase 8 (Execution UI): 10 hours
- Phase 9 (Audit UI): 6 hours
- Phase 10 (Testing): 6 hours
- Phase 11 (Deployment): 4 hours
- **Total**: ~60 hours (1.5-2 weeks for single developer)

## Risk Mitigation
- **AI latency**: Implement timeouts and loading states
- **Camera/mic permissions**: Provide fallback mechanisms
- **Database migrations**: Test thoroughly, backup before production
- **Mobile compatibility**: Test early and often on real devices
