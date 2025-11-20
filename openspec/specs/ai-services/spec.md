# ai-services Specification

## Purpose
TBD - created by archiving change add-ai-service-connectors. Update Purpose after archive.
## Requirements
### Requirement: SambaNova Multimodal Client
**ID**: ai-services-001
**Priority**: High
**Category**: Infrastructure

The system SHALL provide an async HTTP client for SambaNova API multimodal inference.

#### Scenario: Analyze image with text prompt
**Given** a valid SambaNova API key is configured
**And** an image file path is provided
**And** a text prompt is provided
**When** the client sends a multimodal request
**Then** the API returns a text response describing the image
**And** the response is parsed and returned as a string
**And** errors raise appropriate exceptions

**Implementation**:
- Module: `src/infrastructure/ai_services/sambanova.py`
- Function: `async def analyze_image(image_path: str, prompt: str, response_schema: dict | None = None) -> str | dict`
- Uses `httpx.AsyncClient` for HTTP requests
- Reads image file and encodes to base64
- Constructs multimodal message format
- Optionally adds `response_format` with JSON schema if provided
- Parses JSON response and extracts content
- Returns string for standard mode, dict for JSON mode

---

### Requirement: Structured JSON Output with Schema
**ID**: ai-services-007
**Priority**: High
**Category**: Infrastructure

The system SHALL support forcing SambaNova API to return JSON conforming to a provided schema.

#### Scenario: Analyze image with JSON schema output
**Given** a valid SambaNova API key is configured
**And** an image file path is provided
**And** a text prompt is provided
**And** a JSON schema is provided
**When** the client sends a multimodal request with `response_schema` parameter
**Then** the API returns JSON conforming to the schema
**And** the response is parsed and returned as a Python dict
**And** the schema uses `strict: true` mode
**And** no streaming is used

**Implementation**:
- Add `response_schema: dict | None = None` parameter to `analyze_image()`
- When schema is provided, add `response_format` to request body:
  ```python
  {
      "type": "json_schema",
      "json_schema": {
          "name": "response",
          "strict": true,
          "schema": response_schema
      }
  }
  ```
- Parse response as JSON when schema is provided
- Return dict instead of string
- Schema format follows JSON Schema Draft 7
- No streaming support (`stream: false` or omitted)

---

### Requirement: Hume AI Text-to-Speech Client
**ID**: ai-services-002
**Priority**: High
**Category**: Infrastructure

The system SHALL provide an async HTTP client for Hume AI empathic TTS.

#### Scenario: Generate Japanese speech
**Given** a valid Hume AI API key is configured
**And** Japanese text is provided
**When** the client sends a TTS request
**Then** the API returns audio data in MP3 format
**And** the audio is saved to a file
**And** errors raise appropriate exceptions

**Implementation**:
- Module: `src/infrastructure/ai_services/hume.py`
- Function: `async def synthesize_speech(text: str, output_path: str) -> None`
- Uses `httpx.AsyncClient` for HTTP requests
- Sends JSON request with text and voice parameters
- Saves binary response to file
- Supports Japanese language

---

### Requirement: AI Service Configuration
**ID**: ai-services-003
**Priority**: High
**Category**: Configuration

The system SHALL load AI service credentials and endpoints from environment variables.

#### Scenario: Load SambaNova configuration
**Given** `SAMBANOVA_API_KEY` is set in environment
**When** settings are loaded
**Then** the API key is available to the client
**And** the default model is "Llama-4-Maverick-17B-128E-Instruct"
**And** the endpoint is "https://api.sambanova.ai/v1/chat/completions"

#### Scenario: Load Hume AI configuration
**Given** `HUME_AI_API_KEY` and `HUME_AI_SECRET_KEY` are set in environment
**When** settings are loaded
**Then** the API credentials are available to the client
**And** the default voice is configurable
**And** the endpoint is "https://api.hume.ai/v0/tts/inference"

**Implementation**:
- Module: `src/config/settings.py`
- Add `sambanova_api_key: str` field
- Add `sambanova_model: str` field with default
- Add `sambanova_endpoint: str` field with default
- Add `hume_ai_api_key: str` field
- Add `hume_ai_secret_key: str` field
- Add `hume_ai_endpoint: str` field with default

---

### Requirement: Base64 Image Encoding
**ID**: ai-services-004
**Priority**: Medium
**Category**: Infrastructure

The system SHALL encode image files to base64 format for API transmission.

#### Scenario: Encode JPEG image
**Given** a JPEG image file path
**When** the file is read
**Then** the binary content is encoded to base64 string
**And** the data URL format is "data:image/jpeg;base64,{encoded}"

**Implementation**:
- Function: `def encode_image_to_base64(image_path: str) -> str`
- Detects image MIME type from file extension
- Reads binary content
- Encodes with standard library `base64` module
- Returns complete data URL string

---

### Requirement: Error Handling
**ID**: ai-services-005
**Priority**: Medium
**Category**: Infrastructure

The system SHALL handle API errors gracefully with informative exceptions.

#### Scenario: Handle API authentication error
**Given** an invalid API key is configured
**When** a request is made
**Then** an `HTTPStatusError` is raised
**And** the error message includes the status code
**And** the error is logged

#### Scenario: Handle network timeout
**Given** a network timeout occurs
**When** a request is made
**Then** a `TimeoutException` is raised
**And** the error message indicates timeout
**And** the error is logged

**Implementation**:
- Use `httpx.HTTPStatusError` for HTTP errors
- Use `httpx.TimeoutException` for timeouts
- Log errors with `logging` module
- No automatic retry logic (MVP scope)

---

### Requirement: Async Operations
**ID**: ai-services-006
**Priority**: High
**Category**: Infrastructure

The system SHALL use async/await for all I/O operations with AI services.

#### Scenario: Non-blocking API calls
**Given** multiple AI requests need to be made
**When** requests are initiated
**Then** they execute concurrently without blocking
**And** responses are awaited asynchronously
**And** the event loop is not blocked

**Implementation**:
- All API client methods are `async def`
- Use `async with httpx.AsyncClient()` context manager
- Use `await` for all HTTP requests
- Follow FastAPI async best practices

