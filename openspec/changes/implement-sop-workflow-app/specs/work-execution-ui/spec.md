# Work Execution UI Spec

## ADDED Requirements

### Requirement: Camera Preview Interface
**ID**: work-ui-001
**Priority**: Critical
**Category**: Frontend

The system SHALL provide a live camera preview for capturing work evidence.

#### Scenario: Display camera viewfinder
**Given** a work session is active
**When** the execution page loads
**Then** the camera permission is requested
**And** the live camera feed is displayed in the top half of the screen
**And** the current step description is shown in the bottom half
**And** a "ヨシッ!" button is prominently displayed

**Implementation**:
- Component: `app/(auth)/session/execute/[id]/page.tsx`
- API: MediaDevices `getUserMedia({video: {facingMode: 'environment'}})`
- Layout: `grid grid-rows-2` (camera top, info bottom)
- Fallback: Show error message if camera denied

---

### Requirement: Photo Capture
**ID**: work-ui-002
**Priority**: Critical
**Category**: Frontend

The system SHALL capture photos when user confirms step completion.

#### Scenario: Capture photo on "ヨシッ!" button click
**Given** the camera preview is active
**When** the user clicks the "ヨシッ!" button
**Then** a photo is captured from the video stream
**And** the photo is converted to base64
**And** a thumbnail preview is briefly shown
**And** the audio recording starts

**Implementation**:
- Use `<canvas>` to capture frame from `<video>`
- Method: `canvas.toDataURL('image/jpeg', 0.8)`
- Display captured image overlay for 1 second
- Store in state for submission

---

### Requirement: Photo Upload Alternative (Debug Mode)
**ID**: work-ui-002b
**Priority**: Medium
**Category**: Frontend

The system SHALL provide a photo upload option as an alternative to camera capture for testing and accessibility.

#### Scenario: Upload photo instead of using camera
**Given** a work session is active
**And** camera access is denied OR debug mode is enabled
**When** the user clicks "Upload Photo" button
**Then** a file picker opens
**And** the user selects a photo from device storage
**And** the photo is converted to base64
**And** a thumbnail preview is shown

**Implementation**:
- Show "Upload Photo" button as fallback or debug option
- Use `<input type="file" accept="image/*" />`
- Convert uploaded file to base64 using `FileReader.readAsDataURL()`
- Debug toggle: Show upload button when `?debug=true` in URL
- Same data flow: Upload result is sent as `image_base64` to API
- Useful for: Testing with sample photos, environments without camera, accessibility

**Debug Mode Activation**:
```typescript
// URL: /sessions/123?debug=true
const searchParams = useSearchParams();
const debugMode = searchParams.get('debug') === 'true';

{debugMode && (
  <button onClick={handleUpload}>📁 Upload Photo (Debug)</button>
)}
```

---

### Requirement: Audio Recording
**ID**: work-ui-003
**Priority**: High
**Category**: Frontend

The system SHALL record audio confirmations from workers.

#### Scenario: Record audio after button click
**Given** the "ヨシッ!" button has been clicked
**When** audio recording starts
**Then** the microphone permission is requested (if not granted)
**And** audio is recorded for up to 10 seconds
**And** a recording indicator is shown
**And** the user can stop recording early
**And** the audio is converted to base64

**Implementation**:
- API: MediaRecorder with getUserMedia({audio: true})
- Duration: Max 10 seconds, auto-stop
- Format: WebM or MP3 (browser-dependent)
- Convert Blob to base64 before submission
- Show recording timer

---

### Requirement: Text Input Alternative for Audio
**ID**: work-ui-003b
**Priority**: Medium
**Category**: Frontend

The system SHALL provide a text input option as an alternative to audio recording for testing and accessibility.

#### Scenario: Type confirmation instead of recording audio
**Given** a work session is active
**And** microphone access is denied OR debug mode is enabled
**When** the user enters text in the confirmation input
**And** clicks "Submit Check"
**Then** the text is used instead of audio transcript
**And** sent to the backend as the audio description

**Implementation**:
- Show text input field as fallback or debug option
- Placeholder: "例：バルブ閉ヨシッ！" (Example: "Valve closed, Yoshi!")
- Text is sent in the same format as would be transcribed from audio
- Backend treats it identically to Whisper transcription output
- Debug toggle: Show text input when `?debug=true` in URL
- Useful for: Silent environments, testing, accessibility (hearing impaired)

**API Behavior**:
```typescript
// When text input is used instead of audio
POST /api/v1/checks
{
  "session_id": "uuid",
  "step_id": "uuid",
  "image_base64": "data:image/jpeg;base64,...",
  "audio_base64": null,  // No audio data
  "audio_transcript": "バルブ閉ヨシッ！"  // Direct text input
}

// Backend skips Whisper transcription, uses provided text directly
```

**Debug Mode UI**:
```tsx
{debugMode && (
  <div>
    <label>Or type your confirmation:</label>
    <input 
      type="text" 
      placeholder="例：バルブ閉ヨシッ！"
      onChange={(e) => setManualTranscript(e.target.value)}
    />
  </div>
)}
```

---

### Requirement: Safety Check Submission
**ID**: work-ui-004
**Priority**: Critical
**Category**: Frontend

The system SHALL submit captured evidence to the backend for verification.

#### Scenario: Submit check to backend
**Given** a photo and audio have been captured
**When** the submission process starts
**Then** the data is sent to `POST /api/v1/checks`
**And** a loading spinner is displayed
**And** the UI is disabled during processing
**And** the user sees a "Analyzing..." message

**Implementation**:
- API call: `POST /api/v1/checks` with `{session_id, step_id, image_base64, audio_base64}`
- Use React Query mutation
- Optimistic update: Assume pass, revert on fail
- Timeout: 10 seconds, show error if exceeded

---

### Requirement: Feedback Display
**ID**: work-ui-005
**Priority**: High
**Category**: User Experience

The system SHALL display AI feedback visually and audibly.

#### Scenario: Show positive feedback
**Given** a safety check passed
**When** the response is received
**Then** a success message is displayed (green checkmark)
**And** the feedback text is shown (e.g., "しっかり確認できました！")
**And** the feedback audio plays automatically
**And** the next step is highlighted
**And** the "ヨシッ!" button re-enables after 2 seconds

**Implementation**:
- Display: Success icon + feedback text
- Audio: `<audio autoplay src={feedback_audio_url} />`
- Next step: Scroll into view, highlight border
- Re-enable button after audio finishes or 2s timeout

---

#### Scenario: Show corrective feedback
**Given** a safety check failed
**When** the response is received
**Then** a warning message is displayed (yellow/red icon)
**And** the corrective feedback text is shown
**And** the feedback audio plays
**And** the current step remains active
**And** a "Manual Override" button appears

**Implementation**:
- Display: Warning icon + feedback text
- Audio: Play error feedback
- Retry: "ヨシッ!" button allows retry
- Override: Show supervisor override option

---

### Requirement: Manual Override Control
**ID**: work-ui-006
**Priority**: Medium
**Category**: User Control

The system SHALL allow supervisors to manually override failed checks.

#### Scenario: Supervisor overrides failed check
**Given** a check has failed
**And** a supervisor is logged in
**When** they click "Manual Override"
**Then** a reason input dialog appears
**And** they enter an override reason
**And** they confirm the override
**Then** the check result is changed to "override"
**And** the session progresses to the next step

**Implementation**:
- Show override button only if user has supervisor role
- Modal dialog with text input for reason
- API call: `POST /api/v1/checks/{id}/override`
- Update UI state to reflect override

---

### Requirement: Step Progress Indicator
**ID**: work-ui-007
**Priority**: Medium
**Category**: User Experience

The system SHALL show progress through SOP steps.

#### Scenario: Display step progress
**Given** a work session is in progress
**When** the execution UI is displayed
**Then** a progress bar shows completion percentage
**And** completed steps are marked with checkmarks
**And** the current step is highlighted
**And** upcoming steps are visible (grayed out)

**Implementation**:
- Component: Step list sidebar or bottom sheet
- Progress: `{completed_steps} / {total_steps} * 100`
- Visual: Linear progress bar + step list
- Icons: ✓ for completed, ○ for current, • for pending

---

### Requirement: Session Completion Flow
**ID**: work-ui-008
**Priority**: High
**Category**: User Experience

The system SHALL handle session completion gracefully.

#### Scenario: Complete final step
**Given** the user is on the last step
**When** the final check passes
**Then** a completion celebration is shown
**And** the user is prompted to review the session
**And** a "Mark Complete" button is displayed
**When** they click "Mark Complete"
**Then** the session is finalized
**And** they are redirected to the audit view

**Implementation**:
- Detect last step: Check if `next_step === null`
- Celebration: Confetti animation or success screen
- Button: "Mark Session Complete"
- API call: `POST /api/v1/sessions/{id}/complete`
- Redirect: Navigate to `/audit/sessions/{id}`

---

### Requirement: Offline Handling
**ID**: work-ui-009
**Priority**: Low
**Category**: Resilience

The system SHALL provide guidance when network is unavailable.

#### Scenario: Handle network failure during check
**Given** a safety check is submitted
**When** the network is unavailable
**Then** an error message is displayed
**And** the captured data is preserved locally
**And** the user can retry when connection returns

**Implementation**:
- React Query: Retry failed mutations
- Local storage: Save pending checks
- Error message: "Network unavailable. Will retry automatically."
- Out of scope for MVP (nice-to-have)
