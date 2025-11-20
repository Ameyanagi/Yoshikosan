# Safety Check Execution Spec

## ADDED Requirements

### Requirement: Multimodal Safety Verification
**ID**: safety-check-001
**Priority**: Critical
**Category**: Core Feature

The system SHALL verify worker actions using image and audio analysis via AI.

#### Scenario: Execute safety check with photo and audio
**Given** a work session is in progress
**And** the worker has completed a step
**When** they capture a photo and audio recording
**And** submit the check via the API
**Then** the audio is transcribed to text
**And** the entire SOP workflow is loaded for context
**And** the image and transcript are analyzed against expected step with full SOP context
**And** a pass/fail result is returned with feedback
**And** the check is recorded in the database

**Implementation**:
- Endpoint: `POST /api/v1/checks`
- Request: `{session_id, step_id, image_base64, audio_base64}`
- Use case: `src/application/safety_check/execute_safety_check.py`
- Load complete SOP with all tasks and steps for full workflow context
- AI services: SambaNova for transcription + multimodal analysis with full SOP context
- Domain: `src/domain/work_session/entities.py` - `SafetyCheck` entity

---

### Requirement: Audio Transcription
**ID**: safety-check-002
**Priority**: High
**Category**: AI Integration

The system SHALL transcribe worker audio confirmations to text.

#### Scenario: Transcribe Japanese audio confirmation
**Given** audio data from worker (e.g., "バルブ閉ヨシッ！")
**When** the transcription service is invoked
**Then** the SambaNova Whisper model transcribes to text
**And** the transcript is returned in Japanese
**And** the transcript is saved with the safety check

**Implementation**:
- Use SambaNova Whisper-Large-v3 model
- Module: `src/infrastructure/ai_services/sambanova.py`
- Method: `async def transcribe_audio(audio_base64: str) -> str`
- Handle empty/silent audio gracefully

---

### Requirement: Visual Verification
**ID**: safety-check-003
**Priority**: Critical
**Category**: AI Integration

The system SHALL analyze captured images to verify expected results.

#### Scenario: Verify step completion from image
**Given** an image of the work area
**And** the expected step action and result
**And** the complete SOP workflow for full context
**When** the AI analyzes the image
**Then** it determines if the expected result is visible
**And** it verifies the worker is on the correct step (not ahead or behind)
**And** it identifies any safety concerns
**And** it provides confidence score

**Implementation**:
- Use SambaNova multimodal model
- Prompt includes: entire SOP with all tasks/steps, current expected step, hazards
- AI has full workflow context to detect if worker is on wrong step in sequence
- Context length is sufficient for typical SOPs (10-20 steps)
- Response schema: `{result: "pass"|"fail", confidence: float, reasoning: str, step_sequence_correct: bool}`
- See `VERIFY_SAFETY_CHECK_PROMPT` in design.md

---

### Requirement: Contextual Feedback Generation
**ID**: safety-check-004
**Priority**: High
**Category**: User Experience

The system SHALL generate appropriate Japanese feedback based on verification results.

#### Scenario: Generate positive feedback for passed check
**Given** a safety check passed verification
**When** feedback is generated
**Then** the text praises the worker (e.g., "しっかり確認できました！")
**And** the text includes the next step instruction
**And** the tone is encouraging and supportive

**Implementation**:
- Part of AI prompt response
- Feedback stored in `SafetyCheck.feedback_text`
- Next step hint: Look up next step in SOP sequence

---

#### Scenario: Generate corrective feedback for failed check
**Given** a safety check failed verification
**When** feedback is generated
**Then** the text identifies the specific issue
**And** the text provides clear correction instructions
**And** the tone is calm but firm (safety-focused)

**Implementation**:
- AI identifies discrepancy between expected and observed
- Specific examples: "バルブがまだ開いています。もう一度確認してください"
- Reference hazard mitigation if relevant

---

### Requirement: Voice Feedback Synthesis
**ID**: safety-check-005
**Priority**: High
**Category**: AI Integration

The system SHALL convert feedback text to speech using Hume AI for real-time playback.

#### Scenario: Generate voice feedback
**Given** feedback text in Japanese
**When** the TTS service is invoked
**Then** Hume AI synthesizes speech with appropriate emotional tone
**And** the audio is streamed directly to the frontend
**And** audio is NOT stored to disk (MVP simplification)

**Implementation**:
- Use existing `src/infrastructure/ai_services/hume.py`
- Method: `async def synthesize_speech(text: str) -> bytes`
- Return audio bytes directly in API response
- Frontend plays audio immediately
- No persistent storage in MVP

---

### Requirement: Manual Override Capability
**ID**: safety-check-006
**Priority**: Medium
**Category**: User Control

The system SHALL allow supervisors to override AI decisions.

#### Scenario: Supervisor overrides failed check
**Given** a safety check failed AI verification
**And** a supervisor reviews the evidence
**And** determines the check should pass
**When** they submit an override
**Then** the check result is changed to "override"
**And** the override reason is recorded
**And** the supervisor ID is logged
**And** the session can progress to the next step

**Implementation**:
- Endpoint: `POST /api/v1/checks/{id}/override`
- Request: `{result: "pass"|"fail", reason: str}`
- Authorization: Supervisor role required
- Domain method: `WorkSession.override_last_check(reason, supervisor_id)`

---

### Requirement: Check Result Persistence
**ID**: safety-check-007
**Priority**: High
**Category**: Data Integrity

The system SHALL persist all safety check results with audit trail.

#### Scenario: Save safety check to database
**Given** a safety check is completed
**When** the check is persisted
**Then** the following data is saved:
  - Result (pass/fail/override)
  - Feedback text
  - Confidence score
  - Timestamp
  - Override info (if applicable)
**And** the check is linked to the work session and step
**And** images and audio are NOT stored (MVP simplification)

**Implementation**:
- Table: `safety_checks`
- Fields: `id`, `session_id`, `step_id`, `result`, `feedback_text`, `confidence_score`, `needs_review`, `checked_at`, `override_reason`, `override_by`
- Foreign keys: `session_id → work_sessions`, `step_id → steps`, `override_by → users`
- No file storage for images/audio in MVP

---

### Requirement: Check Timeout Handling
**ID**: safety-check-008
**Priority**: Medium
**Category**: Resilience

The system SHALL handle AI service timeouts gracefully.

#### Scenario: AI service times out during check
**Given** a safety check is in progress
**When** the SambaNova API takes longer than 5 seconds
**Then** the request is cancelled
**And** a timeout error is returned to the user
**And** the user can retry the check
**And** the partial data is not saved

**Implementation**:
- HTTP client timeout: 5 seconds for checks
- Error handling in use case
- Return 504 Gateway Timeout with retry message
- No database persistence on timeout

---

### Requirement: Check Confidence Scoring
**ID**: safety-check-009
**Priority**: Low
**Category**: AI Quality

The system SHALL record AI confidence scores for verification decisions.

#### Scenario: Low confidence check triggers warning
**Given** AI analysis completes successfully
**When** the confidence score is below 0.7
**Then** a warning flag is set on the check
**And** the worker is notified to double-check
**And** supervisor review may be requested

**Implementation**:
- Add `confidence_score` field to `safety_checks` table
- Add `needs_review` boolean field
- Threshold: 0.7 (configurable via settings)
- Display warning icon in UI if flagged
