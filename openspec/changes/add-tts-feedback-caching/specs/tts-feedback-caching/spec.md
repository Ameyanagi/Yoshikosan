# Spec: TTS Feedback Caching

## ADDED Requirements

### Requirement: Audio Feedback Persistence

The system MUST persist TTS audio feedback for safety checks to enable replay functionality.

**Rationale**: Workers in noisy industrial environments may miss audio feedback or need to hear safety instructions multiple times. First-time task execution requires clear guidance that can be repeated.

**Dependencies**:
- Existing Hume AI TTS integration
- File system storage (`/tmp` directory)
- Database schema (safety_checks table)

#### Scenario: Worker replays latest feedback audio

**Given**: A worker has completed a safety check and received audio feedback
**When**: The worker clicks the "Replay Last Feedback" button
**Then**: The most recent audio feedback plays through the browser
**And**: The audio can be paused, resumed, or replayed multiple times

**Acceptance Criteria**:
- Audio replay button appears in session execution UI
- Latest audio URL is included in session API responses
- Audio playback uses standard HTML5 Audio API
- Replay does not trigger new AI analysis or TTS generation
- Audio plays on user interaction only (no auto-replay)

---

#### Scenario: Worker replays specific check's feedback

**Given**: A session has multiple safety checks with audio feedback
**When**: The worker views the check history
**Then**: Each check displays a replay button next to its feedback text
**And**: Clicking any replay button plays that check's specific audio
**And**: Multiple audio files can be accessed independently

**Acceptance Criteria**:
- Every check with audio shows a replay button
- Replay buttons are clearly labeled and accessible
- Audio URLs are unique per check (`/api/v1/checks/{check_id}/audio`)
- Audio files remain accessible throughout session lifecycle
- Failed checks' audio is preserved for review

---

#### Scenario: Audio feedback file save fails

**Given**: A worker performs a safety check
**When**: The system attempts to save audio feedback but encounters disk I/O error
**Then**: The safety check still succeeds with feedback text
**And**: No audio replay button is shown for that check
**And**: The error is logged for monitoring

**Acceptance Criteria**:
- Check execution does not fail due to audio save errors
- `feedback_audio_url` is set to `null` if save fails
- Warning message appears in logs with error details
- Worker receives feedback text as normal
- Subsequent checks attempt audio save normally

---

### Requirement: First Task Welcome Audio

The system MUST generate and play welcome audio when a worker starts the first task of a session.

**Rationale**: First-time workers need clear introduction and task overview. Welcome audio sets expectations, reduces anxiety, and establishes voice feedback pattern for the session.

**Dependencies**:
- Start session use case
- Hume AI TTS service
- Session API responses

#### Scenario: Worker starts new session

**Given**: A worker has selected an SOP to begin
**When**: The worker starts a new work session
**Then**: Welcome audio is generated with task title and first step overview
**And**: The audio plays automatically when the session page loads
**And**: The audio includes total step count and safety reminder

**Acceptance Criteria**:
- Welcome audio uses template: "こんにちは！{task_title}を開始します。今日の作業は{total_steps}ステップあります。最初のステップは「{first_step_description}」です。準備ができたら、「ヨシッ！」ボタンを押して確認を始めてください。安全作業、よろしくお願いします！"
- Audio auto-plays on session page load (with fallback for auto-play block)
- Welcome audio is saved to `/tmp/audio/feedback/welcome/{session_id}.mp3`
- Welcome audio can be replayed via button if auto-play is blocked
- Welcome audio generation does not delay session start (async)

---

#### Scenario: Auto-play is blocked by browser

**Given**: A worker starts a new session
**When**: The browser blocks auto-play of welcome audio
**Then**: A prominent "Play Welcome Message" button appears
**And**: Clicking the button plays the welcome audio
**And**: The button disappears after the audio completes

**Acceptance Criteria**:
- Browser auto-play block is detected via promise rejection
- Manual play button is shown immediately
- Button uses clear icon and label (e.g., "🔊 Welcome Message")
- Audio plays successfully on user interaction
- Button state reflects playback status (playing/paused)

---

### Requirement: Audio File Organization

Audio feedback files MUST be organized by session for efficient storage and cleanup.

**Rationale**: Grouping audio files by session enables bulk operations (approval cleanup, session export), simplifies debugging, and provides logical organization for archival.

**Dependencies**:
- File system storage structure
- Session ID from work session entity

#### Scenario: Safety check audio is saved

**Given**: A worker performs a safety check
**When**: The system generates TTS audio feedback
**Then**: Audio is saved to `/tmp/audio/feedback/{session_id}/{check_id}.mp3`
**And**: The directory `/tmp/audio/feedback/{session_id}/` is created if it doesn't exist
**And**: The file has world-readable permissions (644)

**Acceptance Criteria**:
- Audio files are grouped by session ID in directory structure
- Filename uses check ID for uniqueness
- File extension is `.mp3` (Hume AI default format)
- Directories are created recursively with `parents=True`
- File permissions allow web server read access
- File path is stored in database as `feedback_audio_url`

---

#### Scenario: Supervisor reviews completed session

**Given**: A supervisor views a completed session's audit trail
**When**: The supervisor browses check details
**Then**: All audio files for the session are accessible
**And**: Audio URLs follow pattern `/api/v1/checks/{check_id}/audio`
**And**: Files are served with proper MIME type (`audio/mpeg`)

**Acceptance Criteria**:
- Audio endpoint returns `FileResponse` with `media_type="audio/mpeg"`
- Authorization check: only session owner or supervisors can access
- 404 error if audio file is deleted or missing
- Audio files persist after session completion
- Audio URLs are included in audit export (future enhancement)

---

### Requirement: Audio Endpoint Authorization

Access to audio feedback MUST be restricted to authorized users only.

**Rationale**: Audio feedback may contain sensitive work instructions or safety information. Access control prevents unauthorized listening and protects worker privacy.

**Dependencies**:
- User authentication system
- Session ownership data
- Supervisor role

#### Scenario: Session owner accesses their own audio

**Given**: A worker has completed a safety check in their session
**When**: The worker requests audio via `/api/v1/checks/{check_id}/audio`
**Then**: The audio file is served successfully
**And**: Response status is 200 OK
**And**: Content-Type is `audio/mpeg`

**Acceptance Criteria**:
- Worker can access all audio from their own sessions
- No authorization error for owner access
- Audio streams efficiently (no buffering delay)
- Response includes proper headers for audio playback

---

#### Scenario: Unauthorized user attempts to access audio

**Given**: User A has completed a check with audio feedback
**When**: User B (not session owner, not supervisor) requests the audio
**Then**: The request is denied with 403 Forbidden
**And**: No audio data is returned
**And**: An error message states "Access denied"

**Acceptance Criteria**:
- Authorization check before file access
- Session ownership is verified via database query
- Non-owners receive 403 error
- Error response is JSON with clear message
- No file path information is leaked in error

---

#### Scenario: Supervisor accesses worker's audio for review

**Given**: A worker has completed a session with audio feedback
**When**: A supervisor requests audio for audit review
**Then**: The audio file is served successfully
**And**: Supervisor role is verified before granting access

**Acceptance Criteria**:
- Supervisors can access audio from any session
- Role check uses `current_user.is_supervisor` flag
- Supervisors have same audio access as owners
- Audit trail logs supervisor audio access (future enhancement)

---

## MODIFIED Requirements

### Requirement: Safety Check Response Schema (Modified)

**Previously**: Safety check responses included only `feedback_text` without audio reference.

**Now**: Safety check responses MUST include `feedback_audio_url` field for audio replay.

**Change Details**:
- The API MUST add `feedback_audio_url: str | None` to `SafetyCheckResponse` schema
- Field is `null` if audio save failed or was not generated
- URL format: `/api/v1/checks/{check_id}/audio`

#### Scenario: Frontend receives check result with audio URL

**Given**: A worker has submitted a safety check
**When**: The API returns the check result
**Then**: The response includes `feedback_audio_url` field
**And**: Frontend displays both text feedback and replay button

**Example Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "660e8400-e29b-41d4-a716-446655440000",
  "step_id": "770e8400-e29b-41d4-a716-446655440000",
  "result": "pass",
  "feedback_text": "素晴らしい！確認できました。次は部品Bの取り付けです。",
  "feedback_audio_url": "/api/v1/checks/550e8400-e29b-41d4-a716-446655440000/audio",
  "confidence_score": 0.92,
  "needs_review": false,
  "checked_at": "2024-12-20T10:30:45Z"
}
```

---

### Requirement: Work Session Response Schema (Modified)

**Previously**: Session responses included check history but no quick access to latest audio.

**Now**: Session responses MUST include `latest_feedback_audio_url` for immediate replay access.

**Change Details**:
- The API MUST add `latest_feedback_audio_url: str | None` to `WorkSessionDetailResponse`
- Computed from most recent check with non-null `feedback_audio_url`
- Sorted by `checked_at` timestamp descending

#### Scenario: Frontend displays latest feedback replay button

**Given**: A session has multiple checks with audio
**When**: The frontend fetches session details
**Then**: The response includes `latest_feedback_audio_url`
**And**: Frontend displays "Replay Last Feedback" button prominently

**Example Response**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "sop_id": "880e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "current_step_id": "770e8400-e29b-41d4-a716-446655440000",
  "latest_feedback_audio_url": "/api/v1/checks/550e8400-e29b-41d4-a716-446655440000/audio",
  "checks": [
    { "id": "550e8400-...", "feedback_audio_url": "/api/v1/checks/550e8400-.../audio" },
    { "id": "551e8400-...", "feedback_audio_url": "/api/v1/checks/551e8400-.../audio" }
  ]
}
```

---

### Requirement: Session Start Response Schema (Modified)

**Previously**: Session start returned session and first step details only.

**Now**: Session start MUST include `welcome_audio_url` for first task guidance.

**Change Details**:
- The API MUST add `welcome_audio_url: str | None` to `StartSessionResponse`
- URL format: `/api/v1/sessions/{session_id}/welcome-audio`
- Generated only for first task of session

#### Scenario: Worker starts session and receives welcome audio

**Given**: A worker starts a new session
**When**: The start session API responds
**Then**: The response includes `welcome_audio_url`
**And**: Frontend auto-plays the welcome message

**Example Response**:
```json
{
  "session": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "in_progress",
    "current_step_id": "770e8400-e29b-41d4-a716-446655440000"
  },
  "first_step": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "description": "部品Aを確認する"
  },
  "welcome_audio_url": "/api/v1/sessions/660e8400-e29b-41d4-a716-446655440000/welcome-audio"
}
```

---

## REMOVED Requirements

_No requirements removed in this change._
