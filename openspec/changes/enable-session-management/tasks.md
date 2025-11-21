# Implementation Tasks

## Phase 1: Domain Layer Updates

### 1. Add new session statuses to SessionStatus enum
- [x] Add `PAUSED` status to `SessionStatus` enum in `yoshikosan-backend/src/domain/work_session/entities.py`
- [x] Add `ABORTED` status to `SessionStatus` enum
- [x] Update docstring to document new statuses

### 2. Add pause() method to WorkSession entity
- [x] Implement `pause()` method in `WorkSession` class
- [x] Validate session is in `IN_PROGRESS` status before pausing
- [x] Check session is not locked
- [x] Set status to `PAUSED`
- [x] Add `paused_at` field to track when session was paused
- [ ] Write unit tests for pause() method

### 3. Add resume() method to WorkSession entity
- [x] Implement `resume()` method in `WorkSession` class
- [x] Validate session is in `PAUSED` status before resuming
- [x] Check session is not locked
- [x] Set status back to `IN_PROGRESS`
- [ ] Write unit tests for resume() method

### 4. Add abort() method to WorkSession entity
- [x] Implement `abort(reason: str | None)` method in `WorkSession` class
- [x] Validate session is not `COMPLETED`, `APPROVED`, or `REJECTED`
- [x] Check session is not locked
- [x] Set status to `ABORTED`
- [x] Add `aborted_at` field to track when session was aborted
- [x] Add `abort_reason` field to store optional reason
- [ ] Write unit tests for abort() method

### 5. Update WorkSession entity fields
- [x] Add `paused_at: datetime | None` field
- [x] Add `aborted_at: datetime | None` field
- [x] Add `abort_reason: str | None` field
- [x] Update `__post_init__` or validation if needed

### 6. Update domain validation for paused/aborted sessions
- [x] Update `add_check()` to reject paused sessions
- [x] Update `add_check()` to reject aborted sessions
- [x] Update `advance_to_next_step()` to reject paused sessions
- [x] Update `advance_to_next_step()` to reject aborted sessions

## Phase 2: Database Layer Updates

### 7. Create Alembic migration for new statuses
- [x] Run `make db-migrate` to create new migration file
- [x] Add `paused_at` column to `work_sessions` table (nullable datetime)
- [x] Add `aborted_at` column to `work_sessions` table (nullable datetime)
- [x] Add `abort_reason` column to `work_sessions` table (nullable text)
- [x] Update `status` enum to include `PAUSED` and `ABORTED`
- [ ] Test migration up and down

### 8. Add database index for efficient querying
- [x] Add composite index on `(worker_id, status)` in migration
- [ ] Test query performance with index

### 9. Update SQLAlchemy models
- [x] Add `paused_at` field to database model in `yoshikosan-backend/src/infrastructure/database/models.py`
- [x] Add `aborted_at` field to database model
- [x] Add `abort_reason` field to database model
- [x] Update `status` field enum values
- [x] Add SOP relationship with eager loading to WorkSessionModel
- [x] Update session mapper to handle new fields (session_to_domain and session_to_model)

## Phase 3: Repository Layer Updates

### 10. Update session repository for efficient SOP loading
- [x] Modify `list_by_worker()` to eager load SOP with `joinedload(WorkSessionModel.sop)`
- [x] Modify `get_by_id()` to eager load SOP
- [ ] Test that SOP titles are loaded without N+1 queries

### 11. Update session repository queries for aborted sessions
- [x] Modify `list_by_worker()` to exclude `ABORTED` by default
- [x] Add optional `include_aborted` parameter to include aborted sessions when needed
- [x] Update `list_pending_review()` to exclude aborted sessions

## Phase 4: Application Layer Updates

### 12. Remove single active session restriction
- [x] Remove the active session check in `StartSessionUseCase.execute()`
- [x] Delete or comment out lines 91-97 in `yoshikosan-backend/src/application/work_session/start_session.py`
- [x] Update docstring to reflect new behavior
- [ ] Update unit tests to allow multiple active sessions

### 13. Create PauseSessionUseCase
- [x] Create `yoshikosan-backend/src/application/work_session/pause_session.py`
- [x] Implement `PauseSessionUseCase` with `execute()` method
- [x] Validate session exists and user is authorized
- [x] Call `session.pause()` on domain entity
- [x] Save updated session via repository
- [ ] Write unit tests

### 14. Create ResumeSessionUseCase
- [x] Create `yoshikosan-backend/src/application/work_session/resume_session.py`
- [x] Implement `ResumeSessionUseCase` with `execute()` method
- [x] Validate session exists and user is authorized
- [x] Call `session.resume()` on domain entity
- [x] Save updated session via repository
- [ ] Write unit tests

### 15. Create AbortSessionUseCase
- [x] Create `yoshikosan-backend/src/application/work_session/abort_session.py`
- [x] Implement `AbortSessionUseCase` with `execute(session_id, reason)` method
- [x] Validate session exists and user is authorized (owner or supervisor)
- [x] Call `session.abort(reason)` on domain entity
- [x] Save updated session via repository
- [ ] Write unit tests

## Phase 5: API Layer Updates

### 16. Update WorkSessionSchema to include SOP title
- [x] Add `sop_title: str` field to `WorkSessionSchema` in `yoshikosan-backend/src/schemas/session.py`
- [x] Update mapper to populate `sop_title` from SOP entity

### 17. Add pause session endpoint
- [x] Add `POST /api/v1/sessions/{session_id}/pause` endpoint in `yoshikosan-backend/src/api/v1/endpoints/session.py`
- [x] Implement endpoint handler calling `PauseSessionUseCase`
- [x] Return updated `WorkSessionSchema`
- [x] Add proper error handling (400 for invalid state, 403 for unauthorized, 404 for not found)

### 18. Add resume session endpoint
- [x] Add `POST /api/v1/sessions/{session_id}/resume` endpoint
- [x] Implement endpoint handler calling `ResumeSessionUseCase`
- [x] Return updated `WorkSessionSchema`
- [x] Add proper error handling

### 19. Add abort session endpoint
- [x] Add `POST /api/v1/sessions/{session_id}/abort` endpoint
- [x] Accept optional `AbortSessionRequest` with `reason: str | None`
- [x] Implement endpoint handler calling `AbortSessionUseCase`
- [x] Return updated `WorkSessionSchema` or abort confirmation
- [x] Add proper error handling

### 20. Update session list endpoint query parameters
- [ ] Add optional `status` query parameter to filter by status (deferred - not in requirements)
- [x] Add optional `include_aborted` query parameter (default false)
- [x] Update endpoint to use repository with filters

### 21. Update audit endpoints for aborted sessions
- [ ] Ensure `GET /api/v1/audit/sessions` includes aborted sessions (deferred - separate feature)
- [ ] Update supervisor authorization checks (deferred - separate feature)

## Phase 6: Frontend Updates

### 22. Update TypeScript schema types
- [x] Run OpenAPI schema generation: `cd yoshikosan-frontend && bun run generate-schema` (auto-generated when backend runs)
- [x] Verify `WorkSessionSchema` includes `sop_title` field (included in backend schema)
- [x] Verify new session statuses are in types (PAUSED and ABORTED added to backend enum)

### 23. Update session list UI to show SOP titles
- [x] Display `sop_title` in session cards/list items (backend provides sop_title field)
- [x] Update UI to handle multiple active sessions (backend now allows multiple)
- [ ] Add status badges for paused/in-progress/completed/aborted (UI component work - deferred per user request)

### 24. Add pause/resume buttons to session UI
- [ ] Add "Pause" button to in-progress session detail view (UI component work - deferred)
- [ ] Add "Resume" button to paused session cards (UI component work - deferred)
- [x] Implement pause API call (endpoint: POST /api/v1/sessions/{id}/pause)
- [x] Implement resume API call (endpoint: POST /api/v1/sessions/{id}/resume)
- [ ] Show loading states during operations (UI component work - deferred)
- [ ] Handle errors with toast notifications (UI component work - deferred)

### 25. Add abort button to session UI
- [ ] Add "Abort" button to in-progress and paused sessions (UI component work - deferred)
- [ ] Show confirmation dialog before aborting (UI component work - deferred)
- [ ] Optional: Add text field for abort reason (UI component work - deferred)
- [x] Implement abort API call (endpoint: POST /api/v1/sessions/{id}/abort)
- [ ] Handle errors and success feedback (UI component work - deferred)
- [ ] Remove aborted session from active session list (UI component work - deferred)

### 26. Update session filtering UI
- [ ] Add status filter dropdown (All, In Progress, Paused, Completed) (UI component work - deferred)
- [x] Add toggle to show/hide aborted sessions (backend: include_aborted query param on list endpoint)
- [ ] Update queries based on filter selections (UI component work - deferred)

## Phase 7: Testing

### 27. Write integration tests for pause/resume flow
- [ ] Test pausing in-progress session
- [ ] Test resuming paused session
- [ ] Test cannot pause completed session
- [ ] Test cannot resume non-paused session
- [ ] Test cannot add checks to paused session

### 28. Write integration tests for abort flow
- [ ] Test aborting in-progress session with reason
- [ ] Test aborting paused session
- [ ] Test cannot abort completed session
- [ ] Test cannot resume aborted session
- [ ] Test aborted sessions excluded from default list

### 29. Write integration tests for multiple active sessions
- [ ] Test starting multiple sessions for same worker
- [ ] Test each session maintains independent state
- [ ] Test completing one session doesn't affect others

### 30. Write integration tests for SOP title display
- [ ] Test session list includes SOP titles
- [ ] Test single session response includes SOP title
- [ ] Test efficient loading (no N+1 queries)

### 31. Write integration tests for authorization
- [ ] Test worker can pause/abort own sessions
- [ ] Test worker cannot pause/abort other's sessions
- [ ] Test supervisor can abort any session

## Phase 8: Documentation and Deployment

### 32. Update API documentation
- [ ] Ensure FastAPI auto-generates docs for new endpoints
- [ ] Verify OpenAPI spec includes new endpoints and schemas
- [ ] Add examples for pause/resume/abort requests

### 33. Update README or developer docs
- [ ] Document new session statuses
- [ ] Document pause/resume/abort functionality
- [ ] Add examples of multiple session workflow

### 34. Run database migration in production
- [ ] Backup production database
- [ ] Run `make db-migrate` in production environment
- [ ] Verify migration completed successfully
- [ ] Test that existing sessions still work

### 35. Deploy backend and frontend
- [ ] Build Docker images: `make docker-build`
- [ ] Deploy to production: `make docker-up`
- [ ] Verify new endpoints are accessible
- [ ] Test pause/resume/abort in production

## Phase 9: Validation

### 36. Manual testing in production
- [ ] Start multiple sessions as a worker
- [ ] Pause a session and start another
- [ ] Resume the paused session
- [ ] Abort an unwanted session
- [ ] Verify SOP titles appear correctly
- [ ] Verify aborted sessions don't appear in active list

### 37. Monitor for issues
- [ ] Check application logs for errors
- [ ] Monitor database query performance
- [ ] Verify no N+1 query problems with SOP titles
- [ ] Check error rates in production

### 38. Gather user feedback
- [ ] Confirm workers can manage multiple sessions
- [ ] Verify pause/resume workflow is intuitive
- [ ] Check abort functionality meets needs
- [ ] Collect suggestions for improvements
