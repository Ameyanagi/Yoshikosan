# AI Services Integration Tests

This directory contains integration tests for external AI service APIs used by Yoshikosan.

## Overview

These tests validate connectivity and functionality with:
- **SambaNova API**: Multimodal AI (vision + text) using Llama-4-Maverick-17B-128E-Instruct
- **Hume AI API**: Empathic text-to-speech with Japanese language support

**Important**: These are **integration tests** that make real API calls. They require valid API keys and will be skipped if keys are not configured.

## Running Tests

### Run all AI service tests
```bash
make test-ai-services
```

Or directly with pytest:
```bash
cd yoshikosan-backend
uv run pytest tests/ai_services/ -v -s
```

### Run specific tests
```bash
# SambaNova tests only
uv run pytest tests/ai_services/test_sambanova_integration.py -v -s

# Hume AI tests only
uv run pytest tests/ai_services/test_hume_integration.py -v -s
```

## Requirements

### API Keys
Tests require the following environment variables (set in `.env`):

```bash
# SambaNova API
SAMBANOVA_API_KEY=your_api_key_here

# Hume AI
HUME_AI_API_KEY=your_api_key_here
HUME_AI_SECRET_KEY=your_secret_key_here
```

If API keys are not configured, tests will be **skipped** with a clear message.

### Test Data
Tests use sample data from the project:
- **Images**: `data/photo/lego/LEGO_01_OK.JPEG`
- **SOP Text**: `data/SOP/lego/lego_sop.txt`

## Test Results

### Results Directory Structure
Test execution results are automatically saved to timestamped directories:

```
tests/ai_services/results/{timestamp}/
├── metadata.json                  # Test run metadata
├── sambanova_text_request.json    # SambaNova text mode request
├── sambanova_text_response.txt    # SambaNova text mode response
├── sambanova_json_request.json    # SambaNova JSON schema mode request
├── sambanova_json_response.json   # SambaNova JSON schema mode response
├── hume_tts_request.json          # Hume AI TTS request
└── hume_tts_response.mp3          # Generated Japanese audio file
```

### Metadata Format
`metadata.json` contains test execution information:

```json
{
  "timestamp": "2025-11-21T03:00:00.123456",
  "test_name": "sambanova_text",
  "status": "passed",
  "duration_ms": 1234
}
```

### Security
- API keys are **redacted** in saved request files
- Results directory is **gitignored** to prevent accidental commits
- Binary responses (audio) are saved separately

## Test Scenarios

### SambaNova Tests

#### 1. Text Mode (`test_sambanova_analyze_image_text`)
- Analyzes LEGO image with text prompt
- Returns natural language description
- Validates response is non-empty string

#### 2. JSON Schema Mode (`test_sambanova_analyze_image_json_schema`)
- Analyzes LEGO image with structured output
- Uses JSON Schema to enforce response format
- Validates response conforms to schema:
  ```json
  {
    "has_lego": true,
    "description": "Image shows LEGO bricks..."
  }
  ```

### Hume AI Tests

#### 1. Text-to-Speech (`test_hume_synthesize_speech`)
- Synthesizes Japanese text: "こんにちは"
- Uses Fumiko voice (ID: `e5c30713-861d-476e-883a-fc0e1788f736`)
- Generates MP3 audio file
- Validates file exists and size > 0 bytes

## Troubleshooting

### Tests are skipped
- **Cause**: API keys not set in `.env`
- **Fix**: Add required environment variables and restart tests

### Test data not found
- **Cause**: Sample images/SOP files missing
- **Fix**: Ensure `data/photo/lego/` and `data/SOP/lego/` directories exist

### API errors (401 Unauthorized)
- **Cause**: Invalid API keys
- **Fix**: Verify API keys in `.env` are correct

### API errors (429 Rate Limited)
- **Cause**: Too many requests to API
- **Fix**: Wait a moment and retry

### Network timeouts
- **Cause**: Slow network or API downtime
- **Fix**: Check internet connection and API status

## Example Output

```bash
$ make test-ai-services
🤖 Running AI service integration tests...
cd yoshikosan-backend && uv run pytest tests/ai_services/ -v -s

tests/ai_services/test_sambanova_integration.py::test_sambanova_analyze_image_text PASSED

✅ Test passed - Results saved to: /path/to/results/20251121_030000
   Response length: 245 chars
   Duration: 1234ms

tests/ai_services/test_sambanova_integration.py::test_sambanova_analyze_image_json_schema PASSED

✅ Test passed - Results saved to: /path/to/results/20251121_030000
   has_lego: True
   Description: The image shows LEGO bricks...
   Duration: 1567ms

tests/ai_services/test_hume_integration.py::test_hume_synthesize_speech PASSED

✅ Test passed - Results saved to: /path/to/results/20251121_030000
   Text: こんにちは
   Audio file size: 12845 bytes
   Duration: 890ms
   Audio saved to: /path/to/results/20251121_030000/hume_tts_response.mp3

========================= 3 passed in 4.23s =========================
```

## Development Notes

- Tests use `pytest-asyncio` for async support
- Results are saved even if tests fail (for debugging)
- Audio files can be played directly from results directory
- No retry logic implemented (MVP scope)
- No mocking - real API calls only
