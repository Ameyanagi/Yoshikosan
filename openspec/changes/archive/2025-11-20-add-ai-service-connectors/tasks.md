# Tasks: Add AI Service Connectors

## Phase 1: Configuration Setup

### 1.1 Update backend configuration
- [x] Open `yoshikosan-backend/src/config/settings.py`
- [x] Add `sambanova_api_key: str` field
- [x] Add `sambanova_model: str` field with default "Llama-4-Maverick-17B-128E-Instruct"
- [x] Add `sambanova_endpoint: str` field with default "https://api.sambanova.ai/v1/chat/completions"
- [x] Add `hume_ai_api_key: str` field
- [x] Add `hume_ai_secret_key: str` field
- [x] Add `hume_ai_endpoint: str` field with default "https://api.hume.ai/v0/tts/inference"
- [x] Add `hume_ai_voice: str` field with default "e5c30713-861d-476e-883a-fc0e1788f736"  # Fumiko voice
- [x] Verify `.env` has required keys (already present)

**Validation**: Run `python -c "from src.config.settings import settings; print(settings.sambanova_api_key[:10])"` and verify it prints first 10 chars

---

## Phase 2: SambaNova Client

### 2.1 Create infrastructure directory
- [x] Create directory `yoshikosan-backend/src/infrastructure/`
- [x] Create `yoshikosan-backend/src/infrastructure/__init__.py`
- [x] Create directory `yoshikosan-backend/src/infrastructure/ai_services/`
- [x] Create `yoshikosan-backend/src/infrastructure/ai_services/__init__.py`

### 2.2 Implement base64 image encoding utility
- [x] Create `yoshikosan-backend/src/infrastructure/ai_services/utils.py`
- [x] Implement `encode_image_to_base64(image_path: str) -> str`
- [x] Detect MIME type from file extension (.jpg, .jpeg, .png)
- [x] Read file in binary mode
- [x] Encode with `base64.b64encode()`
- [x] Return data URL format: `data:image/{mime};base64,{encoded}`
- [x] Add type hints and docstring

**Validation**: Test with `data/photo/lego/LEGO_01_OK.JPEG` and verify output starts with "data:image/jpeg;base64,"

### 2.3 Implement SambaNova client
- [x] Create `yoshikosan-backend/src/infrastructure/ai_services/sambanova.py`
- [x] Import dependencies: `httpx`, `base64`, `logging`, `json`, settings
- [x] Define `SambanovaClient` class
- [x] Add `__init__` method to initialize with settings
- [x] Implement `async def analyze_image(image_path: str, prompt: str, response_schema: dict | None = None) -> str | dict`
- [x] Encode image to base64
- [x] Construct multimodal message format (text + image_url)
- [x] If `response_schema` is provided, add `response_format` with JSON schema mode
- [x] Set `strict: true` for schema validation
- [x] Ensure streaming is disabled (`stream: false` or omitted)
- [x] Create async HTTP client with auth header
- [x] Send POST request to SambaNova endpoint
- [x] Parse JSON response
- [x] If schema provided, parse and return dict from response content
- [x] If no schema, extract string from choices[0].message.content
- [x] Add error handling for HTTP errors and timeouts
- [x] Add logging for requests and responses
- [x] Add type hints and docstrings

**Validation**: Create test script that:
1. Calls `analyze_image()` with LEGO image and prompt "What do you see in this image?" (returns string)
2. Calls `analyze_image()` with schema `{"type": "object", "properties": {"description": {"type": "string"}}, "required": ["description"]}` (returns dict)

---

## Phase 3: Hume AI Client

### 3.1 Implement Hume AI client
- [x] Create `yoshikosan-backend/src/infrastructure/ai_services/hume.py`
- [x] Import dependencies: `httpx`, `logging`, `pathlib`, settings
- [x] Define `HumeClient` class
- [x] Add `__init__` method to initialize with settings
- [x] Implement `async def synthesize_speech(text: str, output_path: str) -> None`
- [x] Construct JSON request payload with text and voice
- [x] Create async HTTP client with API key auth header
- [x] Send POST request to Hume AI endpoint
- [x] Save binary response to output file
- [x] Add error handling for HTTP errors and timeouts
- [x] Add logging for requests (not binary responses)
- [x] Add type hints and docstrings

**Validation**: Create test script that calls `synthesize_speech("こんにちは", "test.mp3")` and verify MP3 file is created

---

## Phase 4: Test Infrastructure

### 4.1 Create test directory structure
- [x] Create directory `yoshikosan-backend/tests/ai_services/`
- [x] Create `yoshikosan-backend/tests/ai_services/__init__.py`
- [x] Create directory `yoshikosan-backend/tests/ai_services/results/`
- [x] Add `results/` to `.gitignore`

### 4.2 Create test fixtures
- [x] Create `yoshikosan-backend/tests/ai_services/conftest.py`
- [x] Import `pytest`, `pathlib`, `datetime`, `json`
- [x] Define `@pytest.fixture` for `lego_image_path() -> str`
- [x] Define `@pytest.fixture` for `lego_sop_text() -> str`
- [x] Define `@pytest.fixture` for `results_dir() -> str` (creates timestamped directory)
- [x] Implement `save_test_result()` helper function
- [x] Add type hints and docstrings

**Validation**: Run `pytest tests/ai_services/conftest.py::test_fixtures -v` after adding a dummy test

---

## Phase 5: SambaNova Integration Tests

### 5.1 Create SambaNova integration tests
- [x] Create `yoshikosan-backend/tests/ai_services/test_sambanova_integration.py`
- [x] Import `pytest`, `pytest-asyncio`, client classes, fixtures, `json`
- [x] Add `@pytest.mark.asyncio` decorator

**Test 1: Standard text response**
- [x] Define `test_sambanova_analyze_image_text()` test function
- [x] Use `lego_image_path` and `results_dir` fixtures
- [x] Skip test if `SAMBANOVA_API_KEY` not set
- [x] Initialize `SambanovaClient`
- [x] Call `analyze_image()` with test image and prompt (no schema)
- [x] Assert response is non-empty string
- [x] Save request JSON to results directory
- [x] Save response to results directory
- [x] Save metadata JSON with test status and duration
- [x] Add print statement with result location

**Test 2: JSON schema response**
- [x] Define `test_sambanova_analyze_image_json_schema()` test function
- [x] Define JSON schema: `{"type": "object", "properties": {"has_lego": {"type": "boolean"}, "description": {"type": "string"}}, "required": ["has_lego", "description"]}`
- [x] Call `analyze_image()` with test image, prompt, and schema
- [x] Assert response is dict
- [x] Assert "has_lego" and "description" keys exist
- [x] Assert values match schema types
- [x] Save request JSON to results directory
- [x] Save response JSON to results directory
- [x] Save metadata JSON with test status and duration
- [x] Add print statement with result location

**Validation**: Run `pytest tests/ai_services/test_sambanova_integration.py -v -s` and verify:
- Both tests pass
- Results saved to `tests/ai_services/results/{timestamp}/`
- Text mode returns string description
- JSON mode returns dict with schema-conforming structure
- Console shows result directory paths

---

## Phase 6: Hume AI Integration Tests

### 6.1 Create Hume AI integration test
- [x] Create `yoshikosan-backend/tests/ai_services/test_hume_integration.py`
- [x] Import `pytest`, `pytest-asyncio`, client classes, fixtures
- [x] Add `@pytest.mark.asyncio` decorator
- [x] Define `test_hume_synthesize_speech()` test function
- [x] Use `results_dir` fixture
- [x] Skip test if `HUME_AI_API_KEY` not set
- [x] Initialize `HumeClient`
- [x] Call `synthesize_speech("こんにちは", output_path)`
- [x] Assert output file exists and size > 0
- [x] Save request JSON to results directory
- [x] Copy audio file to results directory
- [x] Save metadata JSON with test status and duration
- [x] Add print statement with result location

**Validation**: Run `pytest tests/ai_services/test_hume_integration.py -v -s` and verify:
- Test passes
- MP3 file created and copied to results directory
- File size > 1KB
- Console shows result directory path
- Can play audio file and hear "こんにちは"

---

## Phase 7: Makefile Integration

### 7.1 Add Make target for AI service tests
- [x] Open `Makefile` at project root
- [x] Add `test-ai-services` target
- [x] Command: `cd yoshikosan-backend && uv run pytest tests/ai_services/ -v -s`
- [x] Add help text describing the command
- [x] Add to `.PHONY` declaration

**Validation**: Run `make test-ai-services` and verify both tests execute

---

## Phase 8: Documentation

### 8.1 Create README for test results
- [x] Create `yoshikosan-backend/tests/ai_services/README.md`
- [x] Document test purpose and scope
- [x] Explain results directory structure
- [x] Provide example commands
- [x] Add note about API keys requirement
- [x] Include sample metadata.json format

**Validation**: Review README for clarity and completeness

---

## Phase 9: Final Validation

### 9.1 End-to-end test execution
- [x] Ensure `.env` has valid API keys
- [x] Run `make test-ai-services`
- [x] Verify both SambaNova and Hume tests pass
- [x] Navigate to latest results directory
- [x] Review `metadata.json` files
- [x] Review `sambanova_response.json` for image description
- [x] Play `hume_response.mp3` and verify Japanese audio
- [x] Verify all test artifacts are present and valid

### 9.2 Error case validation
- [x] Temporarily remove API key from `.env`
- [x] Run `make test-ai-services`
- [x] Verify tests are skipped with clear message
- [x] Restore API key

**Validation**: All tests pass or skip appropriately, results are structured and complete

---

## Dependencies
- No new Python packages required (httpx, pytest already in pyproject.toml)
- Requires valid API keys in `.env`
- Requires test data in `data/photo/lego/` and `data/SOP/lego/`

## Estimated Time
- Configuration: 15 minutes
- SambaNova client: 45 minutes
- Hume AI client: 30 minutes
- Test infrastructure: 30 minutes
- Integration tests: 45 minutes
- Makefile + docs: 15 minutes
- **Total**: ~3 hours
