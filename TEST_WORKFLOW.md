# Yoshikosan Workflow Test Guide

This document explains how to test the complete SOP workflow using Playwright.

## Overview

The workflow test covers all 3 phases:

1. **Phase 1 (Pre-Work)**: Upload SOP images → AI structures tasks → User reviews
2. **Phase 2 (Working)**: Execute steps with camera + audio → AI verifies → Feedback
3. **Phase 3 (Post-Work)**: Supervisor reviews audit trail → Approves session

## Test Data

Sample data is provided in `data/`:

- **SOP Images**: `data/SOP/lego/lego_sop1.png`, `lego_sop2.png`
- **Work Photos**: `data/photo/lego/LEGO_01_OK.JPEG` through `LEGO_07_OK.JPEG`
  - OK photos: Expected correct results
  - NG photos: Expected failures (for testing fail scenarios)
- **Audio Sample**: `data/sound/konnichiwa_hume.mp3`

## Prerequisites

1. **Backend running**: `make dev-backend` or `docker-compose up backend`
2. **Frontend running**: `make dev-frontend` or `docker-compose up frontend`
3. **Playwright installed**:
   ```bash
   npm install -D playwright
   npx playwright install chromium
   ```

4. **Test users created**:
   - Worker: `test@example.com` / `testpassword123`
   - Supervisor: `supervisor@example.com` / `supervisor123`

## Running the Test

### Basic Usage

```bash
# Run with default settings (localhost:3000)
node test-workflow.js
```

### Custom Configuration

```bash
# Run against deployed instance
BASE_URL=https://yoshikosan.ameyanagi.com node test-workflow.js

# Run headless (for CI/CD)
HEADLESS=true node test-workflow.js
```

## Test Flow

### Phase 1: SOP Upload

1. Navigate to `/sops/upload`
2. Fill in title: "LEGO Assembly Procedure"
3. Upload 2 SOP images (lego_sop1.png, lego_sop2.png)
4. Optionally add text content
5. Submit form
6. Wait for AI structuring (up to 30 seconds)
7. Verify tasks are displayed
8. Capture SOP ID from URL

**Expected Result**: SOP with multiple tasks and steps displayed

### Phase 2: Work Execution

1. Start new session with SOP ID
2. For each step:
   - Display current step details (description, hazards)
   - Capture photo from camera (mocked with test image)
   - Record audio (mocked with test audio)
   - Click "ヨシッ!" button
   - Send image + audio as base64 to API
   - Wait for AI feedback (up to 10 seconds)
   - Display feedback text
   - Play feedback audio
   - If pass: Advance to next step
   - If fail: Show correction instructions
3. Complete all steps
4. Mark session as complete

**Expected Result**: Session progresses through all steps with AI feedback

### Phase 3: Audit & Approval

1. Logout as worker
2. Login as supervisor
3. Navigate to `/audit`
4. Find completed session
5. Review all safety checks:
   - Timestamps
   - Results (pass/fail)
   - Feedback text
   - Confidence scores
6. Click "Approve Session"
7. Confirm approval
8. Verify session is locked

**Expected Result**: Session approved and locked (immutable)

## Key Architectural Points

### Direct API Upload (No Temp Storage)

The test demonstrates the **base64 direct upload architecture**:

```javascript
// Phase 1: SOP Upload
const image1Base64 = imageToBase64(SOP_IMAGE_1);  // Convert to base64
const image2Base64 = imageToBase64(SOP_IMAGE_2);

// Send as JSON (not multipart/form-data)
await fetch('/api/v1/sops', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'LEGO Assembly',
    images_base64: [image1Base64, image2Base64],  // Base64 strings
    text_content: 'Optional text...'
  })
});
```

```javascript
// Phase 2: Safety Check
const imageBase64 = capturePhotoAsBase64();  // canvas.toDataURL()
const audioBase64 = recordAudioAsBase64();    // MediaRecorder → base64

await fetch('/api/v1/checks', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    step_id: stepId,
    image_base64: imageBase64,  // Direct base64
    audio_base64: audioBase64   // Direct base64
  })
});

// Response includes audio feedback as base64
const response = await fetch(...);
const data = await response.json();

// Play audio directly from base64
const audio = new Audio(`data:audio/mp3;base64,${data.feedback_audio_base64}`);
audio.play();
```

### Benefits of Base64 Architecture

1. **No file storage** during processing
   - Images/audio processed in-memory only
   - No `/tmp` cleanup needed
   - No volume mounts in Docker

2. **Simplified deployment**
   - No persistent storage for evidence
   - Stateless backend (scales horizontally)
   - No storage quota concerns

3. **Privacy-friendly**
   - No PII retention (images/audio discarded after use)
   - Only metadata logged (result, timestamp, feedback text)
   - Complies with data minimization principles

4. **JSON-native**
   - No multipart/form-data parsing
   - Works seamlessly with TypeScript types
   - Easy to test with REST clients

## Expected Output

```
Starting Yoshikosan Workflow Test

Base URL: http://localhost:3000
API URL: http://localhost:8000
✓ Logged in as worker

=== PHASE 1: SOP Upload & Structuring ===

✓ Navigated to SOP upload page
✓ Entered SOP title
✓ Converted images to base64
✓ Selected SOP images
✓ Added optional text content
✓ Submitted SOP upload
✓ AI structuring started
✓ SOP structured successfully
✓ Found 5 tasks in structured SOP
✓ SOP ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

=== PHASE 2: Work Execution ===

✓ Navigated to start session page
✓ Started work session
✓ Session ID: 1a2b3c4d-5e6f-7890-1234-567890abcdef
✓ Mocked camera access

--- Step 1 Safety Check ---
✓ Current step: 部品確認
✓ Captured photo (mocked)
✓ Recorded audio (mocked)
✓ Clicked ヨシッ! button
✓ AI analysis started
✓ Received feedback: しっかり確認できました！次は基礎組み立てです。
✓ Audio feedback playing

--- Step 2 Safety Check ---
...

✓ Session completed

=== PHASE 3: Audit & Approval ===

✓ Logged out as worker
✓ Logged in as supervisor
✓ Navigated to audit page
✓ Opened session audit details
✓ Found 5 safety checks to review
✓ Failed checks: 0
✓ Clicked approve button
✓ Confirmed approval
✓ Session approved successfully
✓ Session is now locked (immutable)

✅ ALL TESTS PASSED ✅
```

## Troubleshooting

### Camera/Microphone Permissions

If running in headless mode, permissions are auto-granted. In headed mode, click "Allow" when prompted.

### AI Timeout

If AI takes longer than 10 seconds, the test will fail. This can happen if:
- SambaNova API is slow
- Hume AI is slow
- Network latency

Increase timeout in test script if needed:
```javascript
await page.waitForSelector('[data-testid="feedback-text"]', { timeout: 30000 });
```

### Session Not Found

Ensure backend and database are running:
```bash
docker-compose up -d postgres
make dev-backend
```

### Images Not Loading

Verify test data exists:
```bash
ls -la data/SOP/lego/
ls -la data/photo/lego/
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: ./wait-for-it.sh localhost:3000 -t 60
      - name: Run workflow test
        run: HEADLESS=true node test-workflow.js
      - name: Upload screenshot on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-failure-screenshot
          path: test-failure.png
```

## Next Steps

1. **Run the test** to verify the workflow works end-to-end
2. **Test failure scenarios** using NG photos (incorrect LEGO assembly)
3. **Measure performance** (AI response times, page load times)
4. **Add more test cases** (edge cases, error handling)
5. **Integrate into CI/CD** for automated regression testing
