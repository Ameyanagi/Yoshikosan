# Design: SOP Workflow Application

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│  Phase 1 UI        Phase 2 UI         Phase 3 UI            │
│  (SOP Upload)      (Execution)        (Audit Review)        │
│                                                              │
│  React Query ←────→ API Client ←────→ Backend API           │
│  Zustand Store     TypeScript Types                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│                    Presentation Layer                        │
│  /api/v1/sops  /api/v1/sessions  /api/v1/checks  /api/v1/audit │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│  StructureSOPUseCase  │  ExecuteSafetyCheckUseCase          │
│  StartSessionUseCase  │  ApproveSessionUseCase              │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│  SOP Aggregate        │  WorkSession Aggregate              │
│  - Task               │  - SafetyCheck                       │
│  - Step               │  - CheckResult                       │
│  - Hazard             │                                      │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│  SQLAlchemy Models    │  AI Service Adapters               │
│  PostgreSQL Repos     │  (SambaNova, Hume AI)              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services & Storage                     │
│  PostgreSQL  │  SambaNova API  │  Hume AI  │  File Storage  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow by Phase

### Phase 1: SOP Upload & Structuring

```
User → Upload SOP (text/images)
  ↓
Frontend converts images to base64
  ↓
POST /api/v1/sops with JSON body:
  {
    title: string,
    images_base64: string[],  // Direct base64 encoding
    text_content: string?
  }
  ↓
StructureSOPUseCase:
  1. Decode base64 images in memory (no file storage)
  2. Call SambaNova with prompt + base64 images directly
  3. Parse JSON response (structured tasks)
  4. Create SOP aggregate with Tasks/Steps/Hazards
  5. Persist to database
  ↓
Return structured SOP JSON
  ↓
Frontend displays editable task list
  ↓
User reviews/edits
  ↓
PUT /api/v1/sops/{id} (if user makes changes)
  ↓
User confirms → POST /api/v1/sessions (start Phase 2)
```

### Phase 2: Work Execution Loop

```
StartSessionUseCase creates WorkSession
  ↓
Frontend enters execution mode:
  - Camera preview (top)
  - Current task/step (bottom)
  - "ヨシッ!" button
  ↓
User performs step → clicks "ヨシッ!"
  ↓
Frontend:
  1. Capture photo from camera (canvas.toDataURL)
     OR upload photo from file picker (debug mode)
  2. Record audio (10 sec or until silence)
     OR type text confirmation (debug mode)
  3. Convert to base64 (no file upload)
  4. Send directly to backend in JSON
  ↓
POST /api/v1/checks
  Request body: {
    session_id, 
    step_id, 
    image_base64: string,      // From camera OR uploaded file
    audio_base64?: string,     // From microphone (optional)
    audio_transcript?: string  // From text input OR Whisper transcription
  }
  ↓
ExecuteSafetyCheckUseCase:
  1. Decode base64 data in memory (no file storage)
  2. Transcribe audio via SambaNova API (base64 input)
  3. Analyze image + audio + expected step via SambaNova (base64 input)
  4. Determine pass/fail + generate feedback
  5. Create SafetyCheck entity (no evidence URLs - data not stored)
  6. If pass → advance session to next step
  7. Generate voice feedback via Hume AI
  8. Return audio bytes directly as base64 in response
  9. Persist check result (timestamp, result, feedback only)
  ↓
Response: {
  result: "pass"|"fail",
  feedback_text: "褒める + 次のステップ" | "是正指示",
  feedback_audio_base64: string,  // Direct base64 audio bytes
  next_step: {...} | null
}
  ↓
Frontend:
  1. Display feedback text
  2. Decode base64 audio and play immediately
  3. Show next step (if pass)
  4. Allow manual override (button)
  ↓
Loop until all steps complete
  ↓
POST /api/v1/sessions/{id}/complete
```

**Key Architectural Decision: No File Storage for Evidence**
- Images and audio are processed in-memory only
- Base64 encoding used for transport (JSON-compatible)
- Evidence is NOT stored to disk during processing
- Only metadata (result, feedback, timestamp) saved to database
- This simplifies deployment (no volume mounts) and privacy (no PII retention)

### Phase 3: Audit & Approval

```
Supervisor opens audit view
  ↓
GET /api/v1/audit/sessions?status=pending
  ↓
Returns list of completed sessions
  ↓
Supervisor selects session
  ↓
GET /api/v1/audit/sessions/{id}
  ↓
Returns full details:
  - All steps with timestamps
  - All safety checks (pass/fail)
  - Image evidence URLs
  - Audio transcript
  ↓
Frontend displays timeline view
  ↓
Supervisor reviews → clicks "Approve"
  ↓
POST /api/v1/audit/sessions/{id}/approve
  ↓
ApproveSessionUseCase:
  1. Mark session as approved
  2. Lock session (immutable)
  3. Set approval timestamp + supervisor ID
  ↓
Session cannot be modified
```

## Database Schema

### Core Tables

```sql
-- SOP Management
CREATE TABLE sops (
  id UUID PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  deleted_at TIMESTAMP
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  sop_id UUID REFERENCES sops(id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  order_index INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE steps (
  id UUID PRIMARY KEY,
  task_id UUID REFERENCES tasks(id),
  description TEXT NOT NULL,
  order_index INTEGER NOT NULL,
  expected_action VARCHAR(255),
  expected_result VARCHAR(255)
);

CREATE TABLE hazards (
  id UUID PRIMARY KEY,
  step_id UUID REFERENCES steps(id),
  description TEXT NOT NULL,
  severity VARCHAR(50), -- low, medium, high, critical
  mitigation TEXT
);

-- Work Execution
CREATE TABLE work_sessions (
  id UUID PRIMARY KEY,
  sop_id UUID REFERENCES sops(id),
  worker_id UUID REFERENCES users(id),
  status VARCHAR(50) NOT NULL, -- in_progress, completed, approved, rejected
  current_step_id UUID REFERENCES steps(id),
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  approved_at TIMESTAMP,
  approved_by UUID REFERENCES users(id),
  locked BOOLEAN DEFAULT FALSE
);

CREATE TABLE safety_checks (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES work_sessions(id),
  step_id UUID REFERENCES steps(id),
  result VARCHAR(50) NOT NULL, -- pass, fail, override
  feedback_text TEXT NOT NULL,
  feedback_audio_url VARCHAR(500),
  image_url VARCHAR(500) NOT NULL,
  audio_transcript TEXT,
  checked_at TIMESTAMP NOT NULL,
  override_reason TEXT,
  override_by UUID REFERENCES users(id)
);

-- Audit Trail
CREATE INDEX idx_sessions_status ON work_sessions(status);
CREATE INDEX idx_checks_session ON safety_checks(session_id);
CREATE INDEX idx_checks_result ON safety_checks(result);
```

## Domain Model Design

### SOP Aggregate (Aggregate Root)

```python
# src/domain/sop/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Hazard:
    id: UUID = field(default_factory=uuid4)
    description: str
    severity: str  # low, medium, high, critical
    mitigation: str | None = None

@dataclass
class Step:
    id: UUID = field(default_factory=uuid4)
    description: str
    order_index: int
    expected_action: str | None = None
    expected_result: str | None = None
    hazards: list[Hazard] = field(default_factory=list)

    def add_hazard(self, description: str, severity: str, mitigation: str | None = None) -> Hazard:
        hazard = Hazard(description=description, severity=severity, mitigation=mitigation)
        self.hazards.append(hazard)
        return hazard

@dataclass
class Task:
    id: UUID = field(default_factory=uuid4)
    title: str
    description: str | None
    order_index: int
    steps: list[Step] = field(default_factory=list)

    def add_step(self, description: str, expected_action: str | None = None) -> Step:
        step = Step(
            description=description,
            order_index=len(self.steps),
            expected_action=expected_action
        )
        self.steps.append(step)
        return step

@dataclass
class SOP:
    """Aggregate Root for SOP domain"""
    id: UUID = field(default_factory=uuid4)
    title: str
    created_by: UUID
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None

    def add_task(self, title: str, description: str | None = None) -> Task:
        task = Task(title=title, description=description, order_index=len(self.tasks))
        self.tasks.append(task)
        return task

    def validate(self) -> list[str]:
        """Business rule validation"""
        errors = []
        if not self.title:
            errors.append("SOP must have a title")
        if not self.tasks:
            errors.append("SOP must have at least one task")
        for task in self.tasks:
            if not task.steps:
                errors.append(f"Task '{task.title}' must have at least one step")
        return errors
```

### WorkSession Aggregate (Aggregate Root)

```python
# src/domain/work_session/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class SessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"

class CheckResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    OVERRIDE = "override"

@dataclass
class SafetyCheck:
    id: UUID = field(default_factory=uuid4)
    step_id: UUID
    result: CheckResult
    feedback_text: str
    feedback_audio_url: str | None
    image_url: str
    audio_transcript: str | None
    checked_at: datetime = field(default_factory=datetime.utcnow)
    override_reason: str | None = None
    override_by: UUID | None = None

@dataclass
class WorkSession:
    """Aggregate Root for work execution"""
    id: UUID = field(default_factory=uuid4)
    sop_id: UUID
    worker_id: UUID
    status: SessionStatus = SessionStatus.IN_PROGRESS
    current_step_id: UUID | None = None
    checks: list[SafetyCheck] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    locked: bool = False

    def add_check(self, step_id: UUID, result: CheckResult, feedback_text: str,
                  image_url: str, **kwargs) -> SafetyCheck:
        if self.locked:
            raise ValueError("Cannot modify locked session")

        check = SafetyCheck(
            step_id=step_id,
            result=result,
            feedback_text=feedback_text,
            image_url=image_url,
            **kwargs
        )
        self.checks.append(check)
        return check

    def advance_to_next_step(self, next_step_id: UUID | None):
        if self.locked:
            raise ValueError("Cannot modify locked session")
        self.current_step_id = next_step_id
        if next_step_id is None:
            self.complete()

    def complete(self):
        if self.locked:
            raise ValueError("Cannot modify locked session")
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def approve(self, supervisor_id: UUID):
        if self.status != SessionStatus.COMPLETED:
            raise ValueError("Can only approve completed sessions")
        if self.locked:
            raise ValueError("Session already locked")

        self.status = SessionStatus.APPROVED
        self.approved_at = datetime.utcnow()
        self.approved_by = supervisor_id
        self.locked = True

    def override_last_check(self, reason: str, supervisor_id: UUID):
        if not self.checks:
            raise ValueError("No checks to override")
        if self.locked:
            raise ValueError("Cannot modify locked session")

        last_check = self.checks[-1]
        last_check.result = CheckResult.OVERRIDE
        last_check.override_reason = reason
        last_check.override_by = supervisor_id
```

## AI Prompts

### SOP Structuring Prompt

```python
STRUCTURE_SOP_PROMPT = """
You are analyzing a Standard Operating Procedure (SOP) or Hazard Prediction (KY/危険予知) document.
Your task is to extract a structured task list with safety information.

Extract:
1. **Title**: Overall task/procedure name
2. **Tasks**: Major steps or phases (preparation → execution → cleanup)
3. **Steps**: Specific actions within each task
4. **Hazards**: For each step, identify:
   - 危険要因 (hazard factors)
   - Severity level (low, medium, high, critical)
   - 対策 (mitigation measures)

Return JSON matching this schema:
{
  "title": "string",
  "tasks": [
    {
      "title": "string",
      "description": "string (optional)",
      "steps": [
        {
          "description": "string",
          "expected_action": "string (what worker should do)",
          "expected_result": "string (what should be verified)",
          "hazards": [
            {
              "description": "string (危険要因)",
              "severity": "low|medium|high|critical",
              "mitigation": "string (対策)"
            }
          ]
        }
      ]
    }
  ]
}

Be thorough and safety-focused. Extract all hazards even if not explicitly labeled.
"""
```

### Safety Verification Prompt

```python
VERIFY_SAFETY_CHECK_PROMPT = """
You are verifying that a worker correctly performed a safety step.

**Complete SOP Workflow:**
{full_sop_structure}

**Current Expected Step (Task {task_number}, Step {step_number}):**
{step_description}
Expected action: {expected_action}
Expected result: {expected_result}
Known hazards: {hazards}

**Worker Evidence:**
- Audio transcript: "{audio_transcript}"
- Image: [provided]
- Timestamp: {timestamp}

**Analysis Required:**
1. Did the worker perform the correct action for THIS step?
2. Does the image show the expected result for THIS step?
3. Did the worker verbally confirm the check? (e.g., "バルブ閉ヨシッ!")
4. Are there any visible safety concerns in the image?
5. Based on the complete workflow, is the worker on the correct step? (Or did they skip/repeat steps?)

Return JSON:
{
  "result": "pass" | "fail",
  "confidence": 0.0-1.0,
  "step_sequence_correct": true | false,
  "feedback_ja": "Japanese feedback (褒める if pass, 是正指示 if fail)",
  "reasoning": "Why you made this determination",
  "next_step_hint": "What to do next (if pass)" | null
}

**Guidelines:**
- Be strict with safety-critical steps
- Use the full SOP context to detect if worker is ahead/behind in the sequence
- If worker appears to be on wrong step, set step_sequence_correct=false and explain in feedback
- Praise good practices (e.g., "しっかり確認できました！")
- Give specific corrections for failures (e.g., "バルブがまだ開いています。もう一度確認してください")
- If out of sequence: "この確認は早すぎます。まず〇〇を完了してください" or "この確認は既に完了しています。次は〇〇です"
- Consider both visual and audio evidence
- The full workflow context helps you understand what should have been done before and what comes after
"""
```

## Alternative Input Methods (Debug Mode)

### Camera Alternative: Photo Upload

**Use Cases:**
- Testing with sample photos from `data/photo/lego/`
- Environments without camera access (desktop browsers, headless tests)
- Accessibility (users who cannot use camera)
- Quality control (upload high-quality reference photos)

**Implementation:**
```tsx
// Enable with URL parameter: /sessions/123?debug=true
const debugMode = useSearchParams().get('debug') === 'true';

function WorkExecutionPage() {
  const [imageSource, setImageSource] = useState<'camera' | 'upload'>('camera');
  
  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Convert to base64 (same format as camera capture)
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      setImageBase64(base64);
    };
    reader.readAsDataURL(file);
  };
  
  return (
    <div>
      {/* Primary: Camera */}
      <video ref={videoRef} autoPlay />
      <button onClick={captureFromCamera}>📷 Capture</button>
      
      {/* Debug Alternative: Upload */}
      {debugMode && (
        <>
          <input 
            type="file" 
            accept="image/*" 
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            ref={fileInputRef}
          />
          <button onClick={() => fileInputRef.current?.click()}>
            📁 Upload Photo (Debug)
          </button>
        </>
      )}
    </div>
  );
}
```

**API Behavior:** Identical - both camera capture and file upload produce `image_base64` string

---

### Microphone Alternative: Text Input

**Use Cases:**
- Testing without audio files
- Silent environments (cannot speak "ヨシッ!")
- Accessibility (hearing/speech impaired users)
- Automated testing with pre-defined confirmations

**Implementation:**
```tsx
function WorkExecutionPage() {
  const [audioSource, setAudioSource] = useState<'mic' | 'text'>('mic');
  const [manualTranscript, setManualTranscript] = useState('');
  
  const handleSubmitCheck = async () => {
    const payload = {
      session_id: sessionId,
      step_id: currentStepId,
      image_base64: imageBase64,
      // Option 1: Audio recorded from microphone
      ...(audioSource === 'mic' && { 
        audio_base64: audioBase64 
      }),
      // Option 2: Text typed manually
      ...(audioSource === 'text' && { 
        audio_transcript: manualTranscript 
      })
    };
    
    await apiClient.checks.execute(payload);
  };
  
  return (
    <div>
      {/* Primary: Microphone */}
      <button onClick={startRecording}>🎤 Record</button>
      
      {/* Debug Alternative: Text */}
      {debugMode && (
        <div>
          <label>Or type confirmation:</label>
          <input
            type="text"
            placeholder="例：バルブ閉ヨシッ！"
            value={manualTranscript}
            onChange={(e) => setManualTranscript(e.target.value)}
          />
        </div>
      )}
    </div>
  );
}
```

**Backend Behavior:**
```python
# In execute_safety_check.py

# If audio_base64 provided: Transcribe with Whisper
if request.audio_base64:
    audio_transcript = await self.ai_client.transcribe_audio(
        audio_base64=request.audio_base64,
        language="ja"
    )
# If audio_transcript provided directly: Use as-is
elif request.audio_transcript:
    audio_transcript = request.audio_transcript
else:
    audio_transcript = ""  # Silent check

# Rest of verification logic remains identical
```

---

### Debug Mode Activation

**URL Parameter:**
```
/sessions/8abe3303-f927-4271-83aa-344d5fdb6c74?debug=true
```

**Environment Variable:**
```bash
# .env.development
NEXT_PUBLIC_DEBUG_MODE=true
```

**Benefits:**
1. **Testing:** Use sample photos from `data/photo/lego/LEGO_01_OK.JPEG`
2. **CI/CD:** Automated tests without hardware dependencies
3. **Accessibility:** Alternative for users without camera/mic
4. **Development:** Faster iteration without device setup

---

## API Endpoint Design

### SOP Management

```
POST   /api/v1/sops                 # Upload and structure SOP
GET    /api/v1/sops                 # List user's SOPs
GET    /api/v1/sops/{id}            # Get SOP details
PUT    /api/v1/sops/{id}            # Update SOP (user edits)
DELETE /api/v1/sops/{id}            # Soft delete SOP
```

### Work Session Management

```
POST   /api/v1/sessions             # Start new work session
GET    /api/v1/sessions             # List user's sessions
GET    /api/v1/sessions/{id}        # Get session details
POST   /api/v1/sessions/{id}/complete  # Mark session complete
```

### Safety Checks

```
POST   /api/v1/checks               # Submit safety check (photo + audio)
GET    /api/v1/checks/{id}          # Get check details
POST   /api/v1/checks/{id}/override # Manual override (supervisor)
```

### Audit & Approval

```
GET    /api/v1/audit/sessions       # List pending approvals (supervisor)
GET    /api/v1/audit/sessions/{id}  # Full session audit trail
POST   /api/v1/audit/sessions/{id}/approve  # Approve session
POST   /api/v1/audit/sessions/{id}/reject   # Reject session
```

## Frontend State Management

### React Query Keys

```typescript
// Query keys for cache invalidation
export const queryKeys = {
  sops: {
    all: ['sops'] as const,
    lists: () => [...queryKeys.sops.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.sops.all, 'detail', id] as const,
  },
  sessions: {
    all: ['sessions'] as const,
    lists: () => [...queryKeys.sessions.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.sessions.all, 'detail', id] as const,
    current: () => [...queryKeys.sessions.all, 'current'] as const,
  },
  audit: {
    all: ['audit'] as const,
    pending: () => [...queryKeys.audit.all, 'pending'] as const,
    detail: (id: string) => [...queryKeys.audit.all, 'detail', id] as const,
  },
};
```

### Zustand Store (Session State)

```typescript
// lib/stores/session-store.ts
import { create } from 'zustand';

interface SessionState {
  sessionId: string | null;
  currentStepIndex: number;
  isRecording: boolean;
  lastFeedback: string | null;

  // Actions
  startSession: (sessionId: string) => void;
  advanceStep: () => void;
  setRecording: (recording: boolean) => void;
  setFeedback: (feedback: string) => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  currentStepIndex: 0,
  isRecording: false,
  lastFeedback: null,

  startSession: (sessionId) => set({ sessionId, currentStepIndex: 0 }),
  advanceStep: () => set((state) => ({ currentStepIndex: state.currentStepIndex + 1 })),
  setRecording: (recording) => set({ isRecording: recording }),
  setFeedback: (feedback) => set({ lastFeedback: feedback }),
  reset: () => set({ sessionId: null, currentStepIndex: 0, isRecording: false, lastFeedback: null }),
}));
```

## Security Considerations

### Authentication & Authorization

- All API endpoints require JWT authentication
- Workers can only access their own SOPs and sessions
- Supervisors have additional permissions:
  - View all sessions (audit)
  - Approve/reject sessions
  - Override safety checks

### Data Privacy

- Images and audio are stored with session-scoped access
- Approved sessions become read-only (immutable audit trail)
- Soft deletes for SOPs (retain audit history)

### Input Validation

- File upload size limits (10MB per file)
- Image format validation (JPEG, PNG only)
- Audio format validation (WebM, MP3, WAV)
- SQL injection protection (SQLAlchemy ORM)
- XSS protection (React escapes by default)

## Performance Considerations

### Backend Optimizations

- Async/await for all I/O (database, AI APIs)
- Database connection pooling (SQLAlchemy)
- Lazy loading of SOP relationships
- Pagination for session lists (limit 20 per page)

### Frontend Optimizations

- React Query caching (5-minute stale time)
- Lazy loading of Phase 2/3 UIs (code splitting)
- Optimistic UI updates (assume check passes)
- Image compression before upload (max 1920x1080)
- Audio compression (max 128kbps)

### AI Service Optimization

- Batch requests when possible
- Timeout limits (5s for checks, 10s for structuring)
- Fallback responses on timeout
- Cache TTS audio (same feedback → same audio)

## Testing Strategy

### Backend Unit Tests

- Domain entities (SOP, WorkSession validation logic)
- Use cases (mocked repositories and AI services)
- Repository implementations (test database)

### Backend Integration Tests

- API endpoints (httpx test client)
- Database migrations (Alembic)
- AI service connectors (already tested)

### Frontend Component Tests

- Upload form validation
- Camera capture flow
- Feedback display

### E2E Tests (Manual MVP, Automated Later)

- Full Phase 1 → 2 → 3 workflow
- Error handling (network failures, AI errors)
- Mobile browser compatibility

## Deployment Notes

- Database migrations run before backend starts
- Static file serving (images, audio) via Nginx
- Environment variables for feature flags
- Monitoring logs for AI latency and errors
