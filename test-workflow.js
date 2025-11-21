/**
 * Playwright Test Script for Yoshikosan SOP Workflow
 *
 * This script tests the complete 3-phase workflow:
 * Phase 1: Upload SOP with images → AI structuring → Review
 * Phase 2: Execute work session with camera + audio checks
 * Phase 3: Supervisor review and approval
 *
 * Uses sample data from data/ directory (LEGO assembly SOP)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';
const TEST_USER_EMAIL = 'test@example.com';
const TEST_USER_PASSWORD = 'testpassword123';
const SUPERVISOR_EMAIL = 'supervisor@example.com';
const SUPERVISOR_PASSWORD = 'supervisor123';

// Test data paths
const DATA_DIR = path.join(__dirname, 'data');
const SOP_IMAGE_1 = path.join(DATA_DIR, 'SOP/lego/lego_sop1.png');
const SOP_IMAGE_2 = path.join(DATA_DIR, 'SOP/lego/lego_sop2.png');
const WORK_PHOTO = path.join(DATA_DIR, 'photo/lego');
const AUDIO_SAMPLE = path.join(DATA_DIR, 'sound/konnichiwa_hume.mp3');

/**
 * Convert image file to base64 data URL
 */
function imageToBase64(filePath) {
  const imageBuffer = fs.readFileSync(filePath);
  const base64 = imageBuffer.toString('base64');
  const ext = path.extname(filePath).toLowerCase();
  const mimeType = ext === '.png' ? 'image/png' : 'image/jpeg';
  return `data:${mimeType};base64,${base64}`;
}

/**
 * Convert audio file to base64 data URL
 */
function audioToBase64(filePath) {
  const audioBuffer = fs.readFileSync(filePath);
  const base64 = audioBuffer.toString('base64');
  return `data:audio/mp3;base64,${base64}`;
}

/**
 * Phase 1: Upload and Structure SOP
 */
async function testPhase1UploadSOP(page) {
  console.log('\n=== PHASE 1: SOP Upload & Structuring ===\n');

  // Navigate to SOP upload page
  await page.goto(`${BASE_URL}/sops/upload`);
  console.log('✓ Navigated to SOP upload page');

  // Fill in SOP title
  await page.fill('input[name="title"]', 'LEGO Assembly Procedure');
  console.log('✓ Entered SOP title');

  // Convert images to base64
  const image1Base64 = imageToBase64(SOP_IMAGE_1);
  const image2Base64 = imageToBase64(SOP_IMAGE_2);
  console.log('✓ Converted images to base64');

  // Upload images (using file input)
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles([SOP_IMAGE_1, SOP_IMAGE_2]);
  console.log('✓ Selected SOP images');

  // Optional: Add text content
  await page.fill('textarea[name="text_content"]',
    'LEGOブロック組み立て手順書\n' +
    '1. 部品確認\n' +
    '2. 基礎組み立て\n' +
    '3. 完成確認'
  );
  console.log('✓ Added optional text content');

  // Submit form
  await page.click('button[type="submit"]');
  console.log('✓ Submitted SOP upload');

  // Wait for AI structuring (show progress)
  await page.waitForSelector('text=Analyzing images', { timeout: 5000 });
  console.log('✓ AI structuring started');

  // Wait for structured SOP display
  await page.waitForURL(/\/sops\/[a-f0-9-]+/, { timeout: 30000 });
  console.log('✓ SOP structured successfully');

  // Verify structured tasks are displayed
  const taskCount = await page.locator('[data-testid="task-item"]').count();
  console.log(`✓ Found ${taskCount} tasks in structured SOP`);

  // Get SOP ID from URL
  const url = page.url();
  const sopId = url.match(/\/sops\/([a-f0-9-]+)/)[1];
  console.log(`✓ SOP ID: ${sopId}`);

  return sopId;
}

/**
 * Phase 2: Execute Work Session with Safety Checks
 */
async function testPhase2WorkExecution(page, sopId) {
  console.log('\n=== PHASE 2: Work Execution ===\n');

  // Start new work session
  await page.goto(`${BASE_URL}/sessions/new?sop_id=${sopId}`);
  console.log('✓ Navigated to start session page');

  await page.click('button:has-text("Start Session")');
  console.log('✓ Started work session');

  // Wait for session page with camera
  await page.waitForURL(/\/sessions\/[a-f0-9-]+/, { timeout: 5000 });
  console.log('✓ Session started');

  const sessionUrl = page.url();
  const sessionId = sessionUrl.match(/\/sessions\/([a-f0-9-]+)/)[1];
  console.log(`✓ Session ID: ${sessionId}`);

  // Simulate camera access
  await page.evaluate(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      return new MediaStream();
    };
  });
  console.log('✓ Mocked camera access');

  // Execute first step
  await testSafetyCheck(page, 1);

  // Execute second step
  await testSafetyCheck(page, 2);

  // Check if session is complete
  const completeButton = await page.locator('button:has-text("Complete Session")');
  if (await completeButton.isVisible()) {
    await completeButton.click();
    console.log('✓ Session completed');
  }

  return sessionId;
}

/**
 * Execute a single safety check
 */
async function testSafetyCheck(page, stepNumber) {
  console.log(`\n--- Step ${stepNumber} Safety Check ---`);

  // Verify current step is displayed
  const stepText = await page.locator('[data-testid="current-step"]').textContent();
  console.log(`✓ Current step: ${stepText}`);

  // Mock camera capture (in real browser, this would capture from video element)
  const workPhotos = fs.readdirSync(WORK_PHOTO);
  const photoPath = path.join(WORK_PHOTO, workPhotos[0]);
  const imageBase64 = imageToBase64(photoPath);
  console.log('✓ Captured photo (mocked)');

  // Mock audio recording
  const audioBase64 = audioToBase64(AUDIO_SAMPLE);
  console.log('✓ Recorded audio (mocked)');

  // Click "ヨシッ!" button
  await page.click('button:has-text("ヨシッ!")');
  console.log('✓ Clicked ヨシッ! button');

  // Wait for AI analysis
  await page.waitForSelector('text=Analyzing', { timeout: 3000 });
  console.log('✓ AI analysis started');

  // Wait for feedback
  await page.waitForSelector('[data-testid="feedback-text"]', { timeout: 10000 });
  const feedbackText = await page.locator('[data-testid="feedback-text"]').textContent();
  console.log(`✓ Received feedback: ${feedbackText.substring(0, 50)}...`);

  // Check if audio feedback is played
  const audioElement = await page.locator('audio[data-testid="feedback-audio"]');
  if (await audioElement.count() > 0) {
    console.log('✓ Audio feedback playing');
  }

  // Wait a moment for feedback to be acknowledged
  await page.waitForTimeout(2000);
}

/**
 * Phase 3: Supervisor Review and Approval
 */
async function testPhase3Audit(page, sessionId) {
  console.log('\n=== PHASE 3: Audit & Approval ===\n');

  // Logout as worker
  await page.click('button:has-text("Logout")');
  console.log('✓ Logged out as worker');

  // Login as supervisor
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[name="email"]', SUPERVISOR_EMAIL);
  await page.fill('input[name="password"]', SUPERVISOR_PASSWORD);
  await page.click('button[type="submit"]');
  console.log('✓ Logged in as supervisor');

  // Navigate to audit page
  await page.goto(`${BASE_URL}/audit`);
  console.log('✓ Navigated to audit page');

  // Find the completed session
  await page.click(`a[href="/audit/${sessionId}"]`);
  console.log('✓ Opened session audit details');

  // Review safety checks
  const checkCount = await page.locator('[data-testid="safety-check-item"]').count();
  console.log(`✓ Found ${checkCount} safety checks to review`);

  // Check for any failed checks
  const failedChecks = await page.locator('[data-testid="check-result"]:has-text("fail")').count();
  console.log(`✓ Failed checks: ${failedChecks}`);

  // Approve session
  await page.click('button:has-text("Approve Session")');
  console.log('✓ Clicked approve button');

  // Confirm approval
  await page.click('button:has-text("Confirm")');
  console.log('✓ Confirmed approval');

  // Wait for success message
  await page.waitForSelector('text=approved', { timeout: 5000 });
  console.log('✓ Session approved successfully');

  // Verify session is locked
  const lockedBadge = await page.locator('text=Locked').count();
  if (lockedBadge > 0) {
    console.log('✓ Session is now locked (immutable)');
  }
}

/**
 * Main test flow
 */
async function runTests() {
  console.log('Starting Yoshikosan Workflow Test\n');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`API URL: ${API_URL}`);

  const browser = await chromium.launch({
    headless: false,  // Set to true for CI/CD
    slowMo: 500       // Slow down actions for visibility
  });

  const context = await browser.newContext({
    permissions: ['camera', 'microphone']
  });

  const page = await context.newPage();

  try {
    // Login as test user (worker)
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/dashboard`);
    console.log('✓ Logged in as worker\n');

    // Execute Phase 1: SOP Upload
    const sopId = await testPhase1UploadSOP(page);

    // Execute Phase 2: Work Execution
    const sessionId = await testPhase2WorkExecution(page, sopId);

    // Execute Phase 3: Audit & Approval
    await testPhase3Audit(page, sessionId);

    console.log('\n✅ ALL TESTS PASSED ✅\n');

  } catch (error) {
    console.error('\n❌ TEST FAILED ❌');
    console.error(error);

    // Take screenshot on failure
    const screenshotPath = path.join(__dirname, 'test-failure.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`\nScreenshot saved to: ${screenshotPath}`);

    throw error;
  } finally {
    await browser.close();
  }
}

// Run tests
runTests().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});
