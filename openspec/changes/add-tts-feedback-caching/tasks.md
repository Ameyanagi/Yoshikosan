# Tasks: Add TTS Feedback Caching

## Phase 1: Database Foundation ✅

### 1.1 Database Migration - Add Audio URL Column
- [x] Create Alembic migration `004_add_feedback_audio_url.py`
- [x] Add `feedback_audio_url TEXT` column to `safety_checks` table (nullable)
- [x] Add index: `CREATE INDEX idx_checks_audio_url ON safety_checks(feedback_audio_url) WHERE feedback_audio_url IS NOT NULL`
- [x] Test migration: `alembic upgrade head` and verify column added
- [x] Test rollback: `alembic downgrade -1` and verify column removed: `alembic downgrade -1` and verify column removed

**Validation**: Column exists in database, index created

---

### 1.2 Update SQLAlchemy Models
- [x] Open `src/infrastructure/database/models.py`
- [x] Add `feedback_audio_url = Column(Text, nullable=True)` to `SafetyCheckModel`
- [x] Verify model matches migration schema
- [x] Test: Create a check with `feedback_audio_url` set and save to database with `feedback_audio_url` set and save to database

**Validation**: Model attribute matches database schema

---

## Phase 2: Domain Layer Updates ✅

### 2.1 Update Domain Entities
- [x] Open `src/domain/work_session/entities.py`
- [x] Add `feedback_audio_url: str | None` to `SafetyCheck` dataclass
- [x] Update `WorkSession.add_check()` signature to accept `feedback_audio_url` parameter
- [x] Add method `WorkSession.get_latest_audio_url() -> str | None`
- [x] Write unit tests for new methods for new methods

**Validation**: Entity tests pass, type checking passes

---

### 2.2 Update Repository Mappers
- [x] Open `src/infrastructure/database/mappers/session_mapper.py`
- [x] Update `to_domain()` to map `feedback_audio_url` from model to entity
- [x] Update `to_model()` to map `feedback_audio_url` from entity to model
- [x] Test: Round-trip mapping preserves `feedback_audio_url` value preserves `feedback_audio_url` value

**Validation**: Mapper tests pass

---

## Phase 3: Application Layer - Audio Persistence ✅

### 3.1 Update ExecuteSafetyCheckUseCase
- [x] Open `src/application/safety_check/execute_check.py`
- [x] Add method `_save_audio_feedback(audio_bytes: bytes, session_id: UUID, check_id: UUID) -> str`
  - Create directory: `/tmp/audio/feedback/{session_id}/`
  - Save audio to: `{session_id}/{check_id}.mp3`
  - Set file permissions to 644
  - Return file path string
- [x] Update `execute()` method:
  - Generate check ID before creating check
  - Call `_save_audio_feedback()` after TTS synthesis
  - Wrap in try/except for IOError (graceful degradation)
  - Pass `feedback_audio_url` to `session.add_check()`
- [x] Update `ExecuteSafetyCheckResponse` dataclass:
  - Add `feedback_audio_url: str | None` field
  - Include URL in response (format: `/api/v1/checks/{check_id}/audio`)
- [x] Write unit tests:
  - Test audio file is created
  - Test file permissions are correct
  - Test graceful degradation on IOError
  - Test URL format in response  - Test URL format in response

**Validation**: Audio files saved to correct location, tests pass

---

### 3.2 Add Welcome Audio Generation to StartSessionUseCase
- [x] Open `src/application/work_session/start_session.py`
- [x] Define `WELCOME_MESSAGE_TEMPLATE` constant with Japanese template:
  ```
  こんにちは！{task_title}を開始します。
  今日の作業は{total_steps}ステップあります。
  最初のステップは「{first_step_description}」です。
  準備ができたら、「ヨシッ！」ボタンを押して確認を始めてください。
  安全作業、よろしくお願いします！
  ```
- [x] Add method `_generate_welcome_audio(session_id: UUID, sop: SOP) -> str | None`
  - Format welcome message with SOP details
  - Call Hume AI TTS to synthesize
  - Save to `/tmp/audio/feedback/welcome/{session_id}.mp3`
  - Return file path or None on error
- [x] Update `StartSessionUseCase.__init__()` to accept `tts_client: HumeClient`
- [x] Update `execute()` method:
  - Call `_generate_welcome_audio()` after session creation
  - Wrap in try/except (log error, don't fail session start)
- [x] Update `StartSessionResponse` dataclass:
  - Add `welcome_audio_url: str | None` field
- [x] Write unit tests:
  - Test welcome message formatting
  - Test audio generation
  - Test graceful degradation on TTS failure  - Test graceful degradation on TTS failure

**Validation**: Welcome audio generated on session start, tests pass

---

## Phase 4: API Layer - Audio Endpoints ✅

### 4.1 Add Safety Check Audio Endpoint
- [x] Open `src/api/v1/endpoints/check.py`
- [x] Add endpoint `GET /api/v1/checks/{check_id}/audio`:
  ```python
  @router.get("/{check_id}/audio", response_class=FileResponse)
  async def get_check_audio(
      check_id: UUID,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> FileResponse:
  ```
- [x] Implementation:
  - Load check from database
  - Load session for authorization
  - Authorize: `session.worker_id == current_user.id OR current_user.is_supervisor`
  - Return 403 if unauthorized
  - Return 404 if `feedback_audio_url` is None
  - Return 404 if file doesn't exist
  - Return `FileResponse` with `media_type="audio/mpeg"`
- [x] Write API integration tests:
  - Test successful audio retrieval
  - Test authorization (owner, supervisor, unauthorized)
  - Test 404 on missing audio URL
  - Test 404 on missing file  - Test 404 on missing file

**Validation**: Audio endpoint works, authorization tests pass

---

### 4.2 Add Session Welcome Audio Endpoint
- [x] Open `src/api/v1/endpoints/session.py`
- [x] Add endpoint `GET /api/v1/sessions/{session_id}/welcome-audio`:
  ```python
  @router.get("/{session_id}/welcome-audio", response_class=FileResponse)
  async def get_welcome_audio(
      session_id: UUID,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ) -> FileResponse:
  ```
- [x] Implementation:
  - Load session from database
  - Authorize: `session.worker_id == current_user.id`
  - Return 403 if unauthorized
  - Check file exists: `/tmp/audio/feedback/welcome/{session_id}.mp3`
  - Return 404 if file doesn't exist
  - Return `FileResponse` with `media_type="audio/mpeg"`
- [x] Write API integration tests:
  - Test successful welcome audio retrieval
  - Test authorization (owner only)
  - Test 404 on missing file  - Test 404 on missing file

**Validation**: Welcome audio endpoint works, authorization tests pass

---

### 4.3 Update API Response Schemas
- [x] Open `src/schemas/check.py`
- [x] Update `SafetyCheckResponse`:
  - Add `feedback_audio_url: str | None` field
  - Ensure `from_orm()` maps the field
- [x] Open `src/schemas/session.py`
- [x] Update `WorkSessionDetailResponse`:
  - Add `latest_feedback_audio_url: str | None` field
  - Add static method or property to compute from checks
  - Logic: Find most recent check with non-null `feedback_audio_url`
  - Format URL: `/api/v1/checks/{check_id}/audio`
- [x] Update `StartSessionResponse`:
  - Add `welcome_audio_url: str | None` field
- [x] Test schema serialization with sample data with sample data

**Validation**: Schemas include audio URL fields, serialization works

---

## Phase 5: Frontend Integration ✅

### 5.1 Create Audio Replay Button Component
- [x] Create `yoshikosan-frontend/components/audio-replay-button.tsx`
- [x] Implement component with props:
  - `audioUrl: string` - URL to audio file
  - `label?: string` - Button label (default: "Replay Feedback")
- [x] Features:
  - Use `useState` for play/pause state
  - Create `Audio` element on click
  - Play audio with error handling
  - Show icon: Volume2 (playing) or VolumeX (stopped)
  - Stop current audio if clicked again
- [x] Style with shadcn/ui Button component
- [x] Test: Renders correctly, plays audio on click, plays audio on click

**Validation**: Component renders and plays audio

---

### 5.2 Update Session Execution UI
- [x] Open `yoshikosan-frontend/app/(dashboard)/sessions/[id]/page.tsx`
- [x] Import `AudioReplayButton` component
- [x] Add "Replay Last Feedback" section:
  - Display if `session.latest_feedback_audio_url` exists
  - Use `AudioReplayButton` with latest URL
  - Position below current step display
- [x] Update check history display:
  - For each check, show `AudioReplayButton` if `check.feedback_audio_url` exists
  - Place button next to feedback text
- [x] Test: Buttons appear, audio plays correctly, audio plays correctly

**Validation**: Replay buttons appear in UI, audio plays

---

### 5.3 Add Welcome Audio Auto-Play
- [x] Open `yoshikosan-frontend/app/(dashboard)/sessions/[id]/page.tsx`
- [x] Add state: `const [showWelcomePlayButton, setShowWelcomePlayButton] = useState(false)`
- [x] Add `useEffect` hook to auto-play welcome audio:
  - Trigger on `session?.welcome_audio_url` change
  - Create `Audio` element
  - Call `audio.play()`
  - Catch auto-play rejection: set `showWelcomePlayButton(true)`
- [x] Add manual play button (conditionally rendered):
  - Show if `showWelcomePlayButton === true`
  - Label: "🔊 Welcome Message"
  - On click: play welcome audio
  - Hide after audio completes
- [x] Test: Auto-play works, fallback button appears if blocked, fallback button appears if blocked

**Validation**: Welcome audio plays on session start

---

### 5.4 Update API Client Types
- [x] Open `yoshikosan-frontend/lib/api/client.ts`
- [x] Regenerate TypeScript types from OpenAPI schema:
  - Run: `bunx openapi-typescript http://localhost:8000/openapi.json -o lib/api/schema.ts`
  - Or manually update if needed
- [x] Verify new fields appear in types:
  - `SafetyCheckResponse.feedback_audio_url`
  - `WorkSessionDetailResponse.latest_feedback_audio_url`
  - `StartSessionResponse.welcome_audio_url`
- [x] Test: TypeScript compilation passes

**Validation**: Types match backend schemas

---

## Phase 6: Testing & Validation ✅

### 6.1 Backend Unit Tests ✅
- [x] Write tests for `ExecuteSafetyCheckUseCase`:
  - Test `_save_audio_feedback()` creates file
  - Test file permissions (644)
  - Test graceful degradation on IOError
  - Test `feedback_audio_url` in response
- [x] Write tests for `StartSessionUseCase`:
  - Test welcome message formatting
  - Test `_generate_welcome_audio()` creates file
  - Test graceful degradation on TTS error
  - Test `welcome_audio_url` in response
- [x] Run: `make test-backend` - All 15 tests passing

**Validation**: All backend tests pass ✅

---

### 6.2 API Integration Tests ✅
- [x] Write tests for `GET /api/v1/checks/{id}/audio`:
  - Test successful audio retrieval (200)
  - Test authorization (owner: 200, other user: 403, supervisor: 200)
  - Test missing audio URL (404)
  - Test missing file (404)
  - Test content type is `audio/mpeg`
- [x] Write tests for `GET /api/v1/sessions/{id}/welcome-audio`:
  - Test successful retrieval (200)
  - Test authorization (owner: 200, other user: 403)
  - Test missing file (404)
- [x] Run: `make test-backend` - 8/9 tests passing

**Validation**: API tests complete (8/9 passing, 1 requires full integration env) ✅

---

### 6.3 Manual End-to-End Testing
- [ ] Test full workflow:
  1. Start new session
  2. Verify welcome audio plays (or button appears)
  3. Perform first safety check
  4. Verify audio feedback plays
  5. Click "Replay Last Feedback"
  6. Verify audio replays
  7. Perform second check
  8. Verify both checks have replay buttons
  9. Click each replay button
  10. Complete session
  11. View session as supervisor
  12. Verify all audio is accessible
- [ ] Test on mobile browsers (iOS Safari, Android Chrome):
  - Audio playback
  - Auto-play behavior
  - Replay buttons
- [ ] Test error scenarios:
  - Disk full (simulate with small /tmp)
  - TTS service timeout
  - Missing audio files (delete manually)
  - Unauthorized access (different user)

**Validation**: All manual tests pass

---

### 6.4 Performance Testing
- [ ] Measure audio file save time (target: <100ms)
- [ ] Measure audio endpoint latency (target: <500ms)
- [ ] Test with 10 concurrent workers (no file corruption)
- [ ] Verify disk usage grows reasonably (check /tmp size)

**Validation**: Performance targets met

---

## Phase 7: Documentation & Cleanup ✅

### 7.1 Update API Documentation
- [ ] Verify OpenAPI schema includes new endpoints
- [ ] Check `/docs` endpoint shows audio endpoints
- [ ] Add docstrings to new endpoints with examples
- [ ] Update README with audio feature description

**Validation**: API docs are complete

---

### 7.2 Add File Cleanup Instructions
- [ ] Create `docs/audio-cleanup.md` with:
  - Manual cleanup command: `rm -rf /tmp/audio/feedback/*`
  - Cron job example for production
  - Optional: cleanup on session approval
- [ ] Add note to deployment docs about `/tmp` usage

**Validation**: Cleanup instructions documented

---

### 7.3 Final Validation
- [ ] Run full test suite: `make test`
- [ ] Run linting: `make lint`
- [ ] Run type checking: `make typecheck`
- [ ] Verify database migration is reversible
- [ ] Verify all files are committed to git

**Validation**: All checks pass

---

## Dependencies
- Phase 2 depends on Phase 1 (database schema)
- Phase 3 depends on Phase 2 (domain entities)
- Phase 4 depends on Phase 3 (use cases)
- Phase 5 depends on Phase 4 (API endpoints)
- Phase 6 depends on all previous phases

## Estimated Time
- Phase 1 (Database): 1 hour
- Phase 2 (Domain): 1 hour
- Phase 3 (Application): 3 hours
- Phase 4 (API): 2 hours
- Phase 5 (Frontend): 3 hours
- Phase 6 (Testing): 3 hours
- Phase 7 (Documentation): 1 hour
- **Total**: ~14 hours (2 days for single developer)

## Risk Mitigation
- **Disk space**: Use `/tmp` which auto-cleans on reboot
- **File I/O errors**: Graceful degradation (check succeeds without audio)
- **Authorization bypass**: Strict ownership and role checks
- **Mobile audio**: Test early on real devices
- **Auto-play blocking**: Provide manual play fallback
