# Design: TTS Feedback Caching

## Architecture Overview

### Current Flow (Without Caching)
```
Worker performs check
  ↓
ExecuteSafetyCheckUseCase
  ↓
Generate feedback text (AI)
  ↓
Synthesize TTS audio (Hume AI) → bytes in memory
  ↓
Return audio bytes in API response
  ↓
Frontend plays audio once
  ↓
Audio discarded (no persistence)
```

### New Flow (With Caching)
```
Worker performs check
  ↓
ExecuteSafetyCheckUseCase
  ↓
Generate feedback text (AI)
  ↓
Synthesize TTS audio (Hume AI) → bytes in memory
  ↓
Save audio bytes to file: /tmp/audio/feedback/{session_id}/{check_id}.mp3
  ↓
Store file URL in database: safety_checks.feedback_audio_url
  ↓
Return check with audio URL
  ↓
Frontend displays replay button
  ↓
Worker can replay audio anytime via GET /api/v1/checks/{id}/audio
```

## Data Model Changes

### Database Schema

```sql
-- Migration: Add feedback_audio_url to safety_checks table
ALTER TABLE safety_checks
ADD COLUMN feedback_audio_url TEXT;

-- Index for quick audio URL lookups
CREATE INDEX idx_checks_audio_url ON safety_checks(feedback_audio_url)
WHERE feedback_audio_url IS NOT NULL;
```

### Updated SafetyCheck Model

```python
# src/infrastructure/database/models.py

class SafetyCheckModel(Base):
    __tablename__ = "safety_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("work_sessions.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("steps.id"), nullable=False)
    result = Column(Text, nullable=False)
    feedback_text = Column(Text, nullable=False)
    feedback_audio_url = Column(Text, nullable=True)  # NEW: URL to audio file
    confidence_score = Column(Float, nullable=True)
    needs_review = Column(Boolean, default=False, nullable=False)
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    override_reason = Column(Text, nullable=True)
    override_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
```

### Domain Entity Update

```python
# src/domain/work_session/entities.py

@dataclass
class SafetyCheck:
    id: UUID = field(default_factory=uuid4)
    step_id: UUID
    result: CheckResult
    feedback_text: str
    feedback_audio_url: str | None  # NEW: URL to persisted audio
    confidence_score: float | None
    needs_review: bool
    checked_at: datetime = field(default_factory=datetime.utcnow)
    override_reason: str | None = None
    override_by: UUID | None = None
```

## File Storage Strategy

### Directory Structure

```
/tmp/audio/feedback/
├── {session_id_1}/
│   ├── {check_id_1}.mp3  # First check audio
│   ├── {check_id_2}.mp3  # Second check audio
│   └── {check_id_3}.mp3  # Third check audio
├── {session_id_2}/
│   ├── {check_id_4}.mp3
│   └── {check_id_5}.mp3
└── welcome/
    └── {session_id}.mp3  # Welcome audio for first task
```

### File Naming Convention

- **Safety check audio**: `/tmp/audio/feedback/{session_id}/{check_id}.mp3`
- **Welcome audio**: `/tmp/audio/feedback/welcome/{session_id}.mp3`
- **URL format**: `/api/v1/checks/{check_id}/audio` (proxied through API)

### Storage Considerations

1. **Location**: `/tmp` directory
   - Automatically cleaned on system reboot
   - No manual cleanup needed for development
   - For production: consider moving to persistent storage or implementing retention policy

2. **File Size**: ~100-300KB per audio file (10-30 seconds)
   - Average session: 5-10 checks = 500KB-3MB total
   - 1000 sessions = 500MB-3GB
   - Manageable for MVP, needs cleanup strategy for production

3. **Permissions**: World-readable (644) for web server access

4. **Concurrency**: Read-only access after creation (no locking needed)

## API Design

### New Endpoint: Serve Audio File

```python
# src/api/v1/endpoints/check.py

@router.get("/{check_id}/audio", response_class=FileResponse)
async def get_check_audio(
    check_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Serve audio feedback file for a safety check.

    Authorization: Only session owner or supervisors can access.
    """
    # Load check with session
    check = await db.get(SafetyCheckModel, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    # Load session for authorization
    session = await db.get(WorkSessionModel, check.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Authorize: owner or supervisor
    if session.worker_id != current_user.id and not current_user.is_supervisor:
        raise HTTPException(status_code=403, detail="Access denied")

    # Return audio file
    if not check.feedback_audio_url:
        raise HTTPException(status_code=404, detail="No audio available")

    audio_path = Path(check.feedback_audio_url)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"feedback_{check_id}.mp3"
    )
```

### Updated Response Schema

```python
# src/schemas/check.py

class SafetyCheckResponse(BaseModel):
    id: UUID
    session_id: UUID
    step_id: UUID
    result: str  # "pass", "fail", "override"
    feedback_text: str
    feedback_audio_url: str | None  # NEW: URL to audio endpoint
    confidence_score: float | None
    needs_review: bool
    checked_at: datetime

    class Config:
        from_attributes = True
```

### Session Response Enhancement

```python
# src/schemas/session.py

class WorkSessionDetailResponse(BaseModel):
    id: UUID
    sop_id: UUID
    worker_id: UUID
    status: str
    current_step_id: UUID | None
    started_at: datetime
    completed_at: datetime | None
    checks: list[SafetyCheckResponse]
    latest_feedback_audio_url: str | None  # NEW: Quick access to latest audio

    @classmethod
    def from_orm_with_latest_audio(cls, session: WorkSessionModel):
        """Create response with latest audio URL computed."""
        latest_audio_url = None
        if session.checks:
            # Get most recent check with audio
            checks_with_audio = [c for c in session.checks if c.feedback_audio_url]
            if checks_with_audio:
                latest_check = max(checks_with_audio, key=lambda c: c.checked_at)
                latest_audio_url = f"/api/v1/checks/{latest_check.id}/audio"

        return cls(
            id=session.id,
            sop_id=session.sop_id,
            worker_id=session.worker_id,
            status=session.status,
            current_step_id=session.current_step_id,
            started_at=session.started_at,
            completed_at=session.completed_at,
            checks=[SafetyCheckResponse.from_orm(c) for c in session.checks],
            latest_feedback_audio_url=latest_audio_url,
        )
```

## Use Case Updates

### ExecuteSafetyCheckUseCase

```python
# src/application/safety_check/execute_check.py

class ExecuteSafetyCheckUseCase:
    async def _save_audio_feedback(
        self,
        audio_bytes: bytes,
        session_id: UUID,
        check_id: UUID
    ) -> str:
        """Save audio feedback to file system.

        Args:
            audio_bytes: Audio data (MP3)
            session_id: Session ID for directory organization
            check_id: Check ID for unique filename

        Returns:
            File path to saved audio

        Raises:
            IOError: If file write fails
        """
        # Create directory structure
        audio_dir = Path("/tmp/audio/feedback") / str(session_id)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Save audio file
        audio_path = audio_dir / f"{check_id}.mp3"
        audio_path.write_bytes(audio_bytes)

        # Set readable permissions
        audio_path.chmod(0o644)

        logger.info(f"Saved audio feedback to {audio_path}")
        return str(audio_path)

    async def execute(
        self, request: ExecuteSafetyCheckRequest
    ) -> ExecuteSafetyCheckResponse:
        """Execute safety check with audio persistence."""

        # ... existing code for AI verification ...

        # Generate voice feedback (existing)
        feedback_audio_bytes = await self._synthesize_audio_feedback(feedback_text)

        # NEW: Save audio to file system
        try:
            check_id = uuid4()  # Generate ID before saving
            audio_url = await self._save_audio_feedback(
                audio_bytes=feedback_audio_bytes,
                session_id=request.session_id,
                check_id=check_id
            )
        except IOError as e:
            # Graceful degradation: log error but continue without audio URL
            logger.error(f"Failed to save audio feedback: {e}")
            audio_url = None

        # Add check to session with audio URL
        session.add_check(
            step_id=request.step_id,
            result=result,
            feedback_text=feedback_text,
            feedback_audio_url=audio_url,  # NEW
            confidence_score=confidence,
            needs_review=needs_review,
        )

        # ... rest of existing code ...

        return ExecuteSafetyCheckResponse(
            result=result,
            feedback_text=feedback_text,
            feedback_audio_bytes=feedback_audio_bytes,  # Still return bytes for immediate play
            feedback_audio_url=f"/api/v1/checks/{check_id}/audio" if audio_url else None,  # NEW
            confidence_score=confidence,
            needs_review=needs_review,
            next_step_id=next_step_id,
            session_updated=session_updated,
        )
```

### WorkSession Entity Update

```python
# src/domain/work_session/entities.py

@dataclass
class WorkSession:
    def add_check(
        self,
        step_id: UUID,
        result: CheckResult,
        feedback_text: str,
        feedback_audio_url: str | None = None,  # NEW parameter
        confidence_score: float | None = None,
        needs_review: bool = False,
    ) -> SafetyCheck:
        if self.locked:
            raise ValueError("Cannot modify locked session")

        check = SafetyCheck(
            step_id=step_id,
            result=result,
            feedback_text=feedback_text,
            feedback_audio_url=feedback_audio_url,  # NEW
            confidence_score=confidence_score,
            needs_review=needs_review,
        )
        self.checks.append(check)
        return check

    def get_latest_audio_url(self) -> str | None:
        """Get the most recent audio feedback URL."""
        checks_with_audio = [c for c in self.checks if c.feedback_audio_url]
        if not checks_with_audio:
            return None

        latest_check = max(checks_with_audio, key=lambda c: c.checked_at)
        return latest_check.feedback_audio_url
```

## First Task Welcome Audio

### Implementation Strategy

When a worker starts a session's **first task** (step 1.1), the system should:
1. Detect that this is the first step
2. Generate welcome message with task overview
3. Synthesize welcome audio using Hume AI
4. Save to `/tmp/audio/feedback/welcome/{session_id}.mp3`
5. Return welcome audio URL alongside task details
6. Frontend auto-plays welcome audio once

### Welcome Message Template

```python
# src/application/work_session/start_session.py

WELCOME_MESSAGE_TEMPLATE = """
こんにちは！{task_title}を開始します。

今日の作業は{total_steps}ステップあります。
最初のステップは「{first_step_description}」です。

準備ができたら、「ヨシッ！」ボタンを押して確認を始めてください。
安全作業、よろしくお願いします！
"""

class StartSessionUseCase:
    async def _generate_welcome_audio(
        self,
        session_id: UUID,
        sop: SOP
    ) -> str | None:
        """Generate welcome audio for first task."""
        first_task = sop.tasks[0]
        first_step = first_task.steps[0]
        total_steps = sum(len(t.steps) for t in sop.tasks)

        # Generate welcome message
        message = WELCOME_MESSAGE_TEMPLATE.format(
            task_title=first_task.title,
            total_steps=total_steps,
            first_step_description=first_step.description,
        )

        # Synthesize audio
        temp_audio_path = Path("/tmp") / f"welcome_{session_id}.mp3"
        await self.tts_client.synthesize_speech(
            text=message,
            output_path=str(temp_audio_path)
        )

        # Save to persistent location
        audio_dir = Path("/tmp/audio/feedback/welcome")
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = audio_dir / f"{session_id}.mp3"
        audio_path.write_bytes(temp_audio_path.read_bytes())
        temp_audio_path.unlink()  # Cleanup temp file

        return str(audio_path)

    async def execute(self, request: StartSessionRequest) -> StartSessionResponse:
        """Start session with welcome audio."""

        # ... existing code to create session ...

        # Generate welcome audio for first task
        welcome_audio_url = None
        try:
            welcome_audio_url = await self._generate_welcome_audio(
                session_id=session.id,
                sop=sop
            )
        except Exception as e:
            logger.error(f"Failed to generate welcome audio: {e}")

        # ... save session ...

        return StartSessionResponse(
            session=session,
            first_step=first_step,
            welcome_audio_url=f"/api/v1/sessions/{session.id}/welcome-audio" if welcome_audio_url else None,
        )
```

### Welcome Audio Endpoint

```python
# src/api/v1/endpoints/session.py

@router.get("/{session_id}/welcome-audio", response_class=FileResponse)
async def get_welcome_audio(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Serve welcome audio for session first task."""

    # Authorize: only session owner
    session = await db.get(WorkSessionModel, session_id)
    if not session or session.worker_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    audio_path = Path(f"/tmp/audio/feedback/welcome/{session_id}.mp3")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Welcome audio not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"welcome_{session_id}.mp3"
    )
```

## Frontend Integration

### Audio Replay Button Component

```tsx
// components/audio-replay-button.tsx

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Volume2, VolumeX } from 'lucide-react';

interface AudioReplayButtonProps {
  audioUrl: string;
  label?: string;
}

export function AudioReplayButton({ audioUrl, label = "Replay Feedback" }: AudioReplayButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  const handleReplay = () => {
    if (audio && !audio.paused) {
      // Stop current playback
      audio.pause();
      audio.currentTime = 0;
      setIsPlaying(false);
    } else {
      // Start playback
      const newAudio = new Audio(audioUrl);
      newAudio.addEventListener('ended', () => setIsPlaying(false));
      newAudio.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        setIsPlaying(false);
      });

      newAudio.play();
      setAudio(newAudio);
      setIsPlaying(true);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleReplay}
      className="gap-2"
    >
      {isPlaying ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
      {label}
    </Button>
  );
}
```

### Session Execution UI Update

```tsx
// app/(dashboard)/sessions/[id]/page.tsx

export default function SessionDetailPage({ params }: { params: { id: string } }) {
  const [session, setSession] = useState<WorkSessionDetailResponse | null>(null);

  // ... fetch session ...

  return (
    <div>
      {/* Current Step Display */}
      <div className="current-step">
        <h2>{currentStep.description}</h2>

        {/* NEW: Latest Feedback Replay */}
        {session.latest_feedback_audio_url && (
          <div className="latest-feedback-replay">
            <AudioReplayButton
              audioUrl={session.latest_feedback_audio_url}
              label="🔊 Replay Last Feedback"
            />
          </div>
        )}
      </div>

      {/* Check History */}
      <div className="check-history">
        {session.checks.map(check => (
          <div key={check.id} className="check-card">
            <p>{check.feedback_text}</p>

            {/* NEW: Per-check replay button */}
            {check.feedback_audio_url && (
              <AudioReplayButton audioUrl={check.feedback_audio_url} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Welcome Audio Auto-Play

```tsx
// app/(dashboard)/sessions/[id]/page.tsx

useEffect(() => {
  // Auto-play welcome audio on first load
  if (session?.welcome_audio_url) {
    const audio = new Audio(session.welcome_audio_url);
    audio.play().catch(e => {
      console.warn('Auto-play blocked:', e);
      // Show manual play button instead
      setShowWelcomePlayButton(true);
    });
  }
}, [session?.id]); // Only trigger on new session
```

## Error Handling

### File Write Failures

```python
# Graceful degradation strategy

try:
    audio_url = await self._save_audio_feedback(audio_bytes, session_id, check_id)
except IOError as e:
    logger.error(f"Failed to save audio feedback: {e}")
    audio_url = None  # Continue without persisted audio

# Check still succeeds, but no replay available
```

### File Not Found

```python
# API endpoint handles missing files

if not audio_path.exists():
    raise HTTPException(
        status_code=404,
        detail="Audio file not found. It may have been cleaned up."
    )
```

### Audio Playback Errors

```tsx
// Frontend handles playback errors gracefully

audio.addEventListener('error', (e) => {
  console.error('Audio playback error:', e);
  toast({
    title: "Audio Unavailable",
    description: "The audio feedback could not be played. You can still read the text feedback above.",
    variant: "warning"
  });
});
```

## Testing Strategy

### Backend Unit Tests

```python
# tests/unit/application/test_execute_check_with_audio.py

async def test_execute_check_saves_audio_file():
    """Test that audio feedback is saved to file system."""
    use_case = ExecuteSafetyCheckUseCase(...)
    request = ExecuteSafetyCheckRequest(...)

    response = await use_case.execute(request)

    # Assert audio file exists
    assert response.feedback_audio_url is not None
    audio_path = Path(response.feedback_audio_url)
    assert audio_path.exists()
    assert audio_path.suffix == ".mp3"

    # Cleanup
    audio_path.unlink()

async def test_execute_check_graceful_degradation_on_io_error():
    """Test that check succeeds even if audio save fails."""
    use_case = ExecuteSafetyCheckUseCase(...)

    # Mock file write to raise IOError
    with patch('pathlib.Path.write_bytes', side_effect=IOError("Disk full")):
        response = await use_case.execute(request)

    # Check still succeeds
    assert response.result == CheckResult.PASS
    # But no audio URL
    assert response.feedback_audio_url is None
```

### Integration Tests

```python
# tests/integration/api/test_audio_endpoints.py

async def test_get_check_audio_returns_file(client: AsyncClient):
    """Test audio endpoint serves MP3 file."""
    # Create check with audio
    check_id = await create_test_check_with_audio()

    # GET audio endpoint
    response = await client.get(f"/api/v1/checks/{check_id}/audio")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 0  # Non-empty audio

async def test_get_check_audio_authorization(client: AsyncClient):
    """Test that only session owner can access audio."""
    # Create check as user A
    check_id = await create_test_check(user_id=user_a_id)

    # Try to access as user B
    response = await client.get(
        f"/api/v1/checks/{check_id}/audio",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )

    assert response.status_code == 403
```

### Frontend Tests

```tsx
// tests/components/audio-replay-button.test.tsx

test('AudioReplayButton plays audio on click', async () => {
  const mockAudioUrl = '/api/v1/checks/123/audio';
  render(<AudioReplayButton audioUrl={mockAudioUrl} />);

  const button = screen.getByRole('button', { name: /replay/i });
  fireEvent.click(button);

  // Assert Audio API called
  expect(HTMLAudioElement).toHaveBeenCalledWith(mockAudioUrl);
  expect(mockAudio.play).toHaveBeenCalled();
});
```

## Production Considerations

### File Cleanup Strategy

For production deployment, implement periodic cleanup:

```bash
# Cron job to clean old audio files (retain 30 days)
0 2 * * * find /tmp/audio/feedback -type f -mtime +30 -delete

# Or clean up on session approval
# In ApproveSessionUseCase:
async def execute(self, request):
    session = await self.session_repository.get_by_id(request.session_id)
    session.approve(request.supervisor_id)

    # Optional: Delete audio files after approval
    for check in session.checks:
        if check.feedback_audio_url:
            Path(check.feedback_audio_url).unlink(missing_ok=True)

    await self.session_repository.save(session)
```

### Cloud Storage Migration

For scale, migrate from local file system to cloud storage:

```python
# Future: S3 storage adapter
class S3AudioStorage:
    async def save_audio(self, audio_bytes: bytes, key: str) -> str:
        """Upload to S3 and return CDN URL."""
        await self.s3_client.put_object(
            Bucket="yoshikosan-audio",
            Key=key,
            Body=audio_bytes,
            ContentType="audio/mpeg"
        )
        return f"https://cdn.yoshikosan.com/audio/{key}"
```

### Monitoring

Track audio-related metrics:
- Audio file save success rate
- Audio file size distribution
- Replay frequency per session
- Storage disk usage

```python
# Add metrics to use case
logger.info(f"Audio saved: size={len(audio_bytes)} bytes, session={session_id}")
```
