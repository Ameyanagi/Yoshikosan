# Proposal: Add AI Service Connectors

## Why

The Yoshikosan safety management system requires integration with two external AI services to provide core functionality:

1. **SambaNova API** - For multimodal AI analysis (vision + text)
   - Model: Llama-4-Maverick-17B-128E-Instruct (multimodal vision+text capabilities)
   - Use case: Analyzing worker photos with SOP context to verify safety compliance
   - Also provides Whisper-Large-v3 for speech-to-text (future use)

2. **Hume AI API** - For empathic text-to-speech
   - Provides emotionally intelligent voice feedback
   - Use case: Giving workers audio feedback with appropriate emotional tone (calm guidance vs. urgent warnings)
   - Japanese language support with natural-sounding voice

Currently, these services are defined in `.env` but not yet integrated into the backend. This proposal creates minimal, testable connectors to validate API connectivity and basic functionality before building higher-level features.

## What Changes

### Backend Infrastructure Layer
Create AI service adapter modules in `yoshikosan-backend/src/infrastructure/ai_services/`:

1. **SambaNova Connector** (`sambanova.py`)
   - HTTP client for SambaNova API
   - Multimodal request handling (image + text prompts)
   - Response parsing and error handling
   - Test with LEGO SOP images and text

2. **Hume AI Connector** (`hume.py`)
   - HTTP client for Hume AI TTS API
   - Japanese text-to-speech generation
   - Audio response handling
   - Test with simple Japanese phrase ("こんにちは")

3. **Test Results Storage** (`tests/ai_services/`)
   - Structured output directory for test results
   - JSON response logs
   - Generated audio files
   - Test execution reports

### Configuration
- Read API keys from environment variables (already in `.env`)
- Add API endpoints and model configurations to `src/config/settings.py`

### Testing
- Integration tests that call real APIs
- Test results saved to `tests/ai_services/results/` directory
- Include timestamps, request/response payloads, and generated outputs

## Out of Scope
- Domain layer integration (SOP verification use cases)
- Application layer services
- Frontend integration
- Advanced prompt engineering
- Error retry logic and circuit breakers (minimal error handling only)
- Production-grade logging and monitoring
