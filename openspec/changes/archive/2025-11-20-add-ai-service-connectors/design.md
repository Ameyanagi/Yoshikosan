# Design: AI Service Connectors

## Architecture Decision

### Adapter Pattern
Place AI service clients in the **infrastructure layer** (`src/infrastructure/ai_services/`) following DDD principles:

```
src/infrastructure/ai_services/
├── __init__.py
├── sambanova.py      # SambaNova API client
└── hume.py           # Hume AI TTS client
```

**Rationale**:
- Infrastructure layer handles external service integrations
- Keeps domain layer pure (no external dependencies)
- Allows easy mocking for domain/application layer tests
- Follows existing authentication pattern (`src/domain/user/`)

### Technology Choices

**HTTP Client**: `httpx` (async)
- Already in dependencies (`httpx>=0.27.0`)
- Async/await support for non-blocking API calls
- Clean API for multipart requests (image uploads)

**Image Encoding**: Base64
- SambaNova expects base64-encoded images in JSON
- Standard library `base64` module

**Configuration**: Pydantic Settings
- Extend existing `src/config/settings.py`
- Type-safe environment variable access
- Already used for OAuth and database config

## API Integration Patterns

### SambaNova (Multimodal Vision)

**Endpoint**: `https://api.sambanova.ai/v1/chat/completions`

**Request Format (Standard)**:
```python
{
    "model": "Llama-4-Maverick-17B-128E-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
}
```

**Request Format (JSON Mode with Schema)**:
```python
{
    "model": "Llama-4-Maverick-17B-128E-Instruct",
    "messages": [...],
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "safety_check_result",
            "strict": true,
            "schema": {
                "type": "object",
                "properties": {
                    "compliant": {"type": "boolean"},
                    "issues": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["compliant", "issues"],
                "additionalProperties": false
            }
        }
    }
}
```

**Note**: No streaming support needed for MVP.

**Response Format**:
```python
{
    "choices": [
        {
            "message": {
                "content": "AI response text"
            }
        }
    ]
}
```

### Hume AI (Empathic TTS)

**Endpoint**: `https://api.hume.ai/v0/tts/inference`

**Request Format**:
```python
{
    "text": "こんにちは",
    "voice": "e5c30713-861d-476e-883a-fc0e1788f736",  # Fumiko - Japanese female voice
    "format": "mp3"
}
```

**Response Format**:
- Binary audio data (MP3)
- Content-Type: audio/mpeg

## Test Strategy

### Integration Testing Approach
Unlike unit tests, these tests call real APIs to validate connectivity:

**Test Structure**:
```
tests/ai_services/
├── __init__.py
├── test_sambanova_integration.py
├── test_hume_integration.py
└── results/                    # Output directory
    ├── {timestamp}/
    │   ├── metadata.json       # Test run info
    │   ├── sambanova_response.json
    │   ├── sambanova_request.json
    │   ├── hume_response.mp3
    │   └── hume_request.json
```

**Test Data Sources**:
- Images: `data/photo/lego/LEGO_01_OK.JPEG`
- SOP Text: `data/SOP/lego/lego_sop.txt`

**Test Execution**:
```bash
pytest tests/ai_services/ -v --capture=no
```

### Result Storage Format

**metadata.json**:
```json
{
    "timestamp": "2025-11-21T03:00:00Z",
    "test_name": "test_sambanova_vision",
    "status": "passed",
    "duration_ms": 1234,
    "api_keys_present": {
        "sambanova": true,
        "hume": true
    }
}
```

## Error Handling

### Minimal Error Handling (MVP)
- Raise exceptions on API errors (no retry logic)
- Log errors to console
- Save error responses to results directory

### Future Enhancements (Out of Scope)
- Retry logic with exponential backoff
- Circuit breaker pattern
- Rate limiting
- Response caching
- Structured logging to file/database

## Security Considerations

### API Key Management
- Keys stored in `.env` (gitignored)
- Loaded via Pydantic Settings
- Never logged or saved to results
- Masked in test output (`SAMBA***`)

### Data Privacy
- Test images are sample LEGO data (non-sensitive)
- Real worker photos will require encryption at rest
- API requests over HTTPS only

## Dependencies

### New Dependencies
None - all required packages already in `pyproject.toml`:
- `httpx>=0.27.0` (async HTTP client)
- `pydantic-settings>=2.6.0` (configuration)
- `pytest>=8.3.0` (testing)

### File Dependencies
Test data:
- `data/photo/lego/*.JPEG` (worker simulation photos)
- `data/SOP/lego/lego_sop.txt` (SOP text)
