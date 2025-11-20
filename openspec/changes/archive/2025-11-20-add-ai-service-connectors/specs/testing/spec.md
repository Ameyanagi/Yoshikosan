# Testing Spec

## ADDED Requirements

### Requirement: Integration Test Suite
**ID**: testing-001
**Priority**: High
**Category**: Testing

The system SHALL provide integration tests that validate AI service connectivity.

#### Scenario: Test SambaNova multimodal analysis
**Given** test image data exists at `data/photo/lego/LEGO_01_OK.JPEG`
**And** test SOP text exists at `data/SOP/lego/lego_sop.txt`
**When** the integration test runs
**Then** the SambaNova client analyzes the image with text
**And** a valid response is received
**And** the request and response are saved to results directory
**And** the test passes

#### Scenario: Test Hume AI speech synthesis
**Given** test text is "こんにちは"
**When** the integration test runs
**Then** the Hume AI client generates Japanese speech
**And** an MP3 file is created
**And** the file is saved to results directory
**And** the test passes

**Implementation**:
- Module: `tests/ai_services/test_sambanova_integration.py`
- Module: `tests/ai_services/test_hume_integration.py`
- Use `pytest` test framework
- Use `pytest-asyncio` for async test support
- Real API calls (not mocked)
- Skip tests if API keys not configured

---

### Requirement: Structured Test Results
**ID**: testing-002
**Priority**: Medium
**Category**: Testing

The system SHALL save test execution results in a structured format for review.

#### Scenario: Save test run metadata
**Given** an integration test executes
**When** the test completes
**Then** a timestamped directory is created in `tests/ai_services/results/`
**And** a `metadata.json` file is created with test info
**And** the metadata includes test name, status, duration, and timestamp

#### Scenario: Save API request and response
**Given** an AI service API call is made during testing
**When** the call completes
**Then** the request payload is saved as `{service}_request.json`
**And** the response is saved as `{service}_response.json` or `.mp3`
**And** sensitive data (API keys) is redacted

**Implementation**:
- Results directory: `tests/ai_services/results/{timestamp}/`
- Metadata format:
  ```json
  {
    "timestamp": "ISO 8601",
    "test_name": "str",
    "status": "passed|failed|skipped",
    "duration_ms": "int",
    "api_keys_present": {"sambanova": "bool", "hume": "bool"}
  }
  ```
- Helper function: `save_test_result(name, request, response, status)`

---

### Requirement: Test Data Management
**ID**: testing-003
**Priority**: Medium
**Category**: Testing

The system SHALL use existing sample data for integration testing.

#### Scenario: Load LEGO test images
**Given** sample LEGO images exist in `data/photo/lego/`
**When** tests need image data
**Then** `LEGO_01_OK.JPEG` is used as the default test image
**And** the file path is resolved relative to project root

#### Scenario: Load SOP text
**Given** sample SOP text exists at `data/SOP/lego/lego_sop.txt`
**When** tests need SOP context
**Then** the file content is read and used as text prompt
**And** the file path is resolved relative to project root

**Implementation**:
- Test fixtures in `tests/ai_services/conftest.py`
- Fixture: `lego_image_path() -> str` returns absolute path
- Fixture: `lego_sop_text() -> str` returns file content
- Use `pathlib.Path` for cross-platform paths

---

### Requirement: Test Execution Commands
**ID**: testing-004
**Priority**: Low
**Category**: Testing

The system SHALL support running AI integration tests via Make commands.

#### Scenario: Run all AI service tests
**Given** Make commands are configured
**When** `make test-ai-services` is executed
**Then** all integration tests run
**And** results are displayed in console
**And** results are saved to results directory

#### Scenario: View test results
**Given** tests have been executed
**When** results directory is accessed
**Then** latest test run directory is identifiable by timestamp
**And** all artifacts (JSON, MP3) are present

**Implementation**:
- Makefile target: `test-ai-services`
- Command: `pytest tests/ai_services/ -v --capture=no`
- Results automatically saved by test fixtures
- Console output shows test status and result locations

---

### Requirement: API Key Validation
**ID**: testing-005
**Priority**: Medium
**Category**: Testing

The system SHALL skip integration tests when API keys are not configured.

#### Scenario: Skip tests without credentials
**Given** AI service API keys are not set in environment
**When** integration tests run
**Then** tests are marked as skipped with clear message
**And** no API calls are attempted
**And** test suite does not fail

#### Scenario: Validate credentials before testing
**Given** API keys are configured
**When** integration tests run
**Then** credentials are validated (format check only)
**And** tests proceed if format is valid
**And** helpful error message is shown if format is invalid

**Implementation**:
- Use `pytest.skip()` decorator with condition
- Check: `if not settings.sambanova_api_key: pytest.skip(...)`
- Validation: Check key is non-empty string
- Error message: "SAMBANOVA_API_KEY not set in environment"
