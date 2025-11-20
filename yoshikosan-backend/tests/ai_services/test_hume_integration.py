"""Integration tests for Hume AI TTS client."""

import shutil
import time
from pathlib import Path

import pytest

from src.config.settings import settings
from src.infrastructure.ai_services.hume import HumeClient
from tests.ai_services.conftest import save_test_result


@pytest.mark.asyncio
async def test_hume_synthesize_speech(results_dir: Path) -> None:
    """Test Hume AI speech synthesis."""
    # Skip if API key not configured
    if not settings.HUME_AI_API_KEY or not settings.HUME_AI_SECRET_KEY:
        pytest.skip("HUME_AI_API_KEY or HUME_AI_SECRET_KEY not set in environment")

    client = HumeClient()
    test_text = "こんにちは"

    # Create temporary output path
    temp_output = results_dir / "temp_output.mp3"

    # Measure execution time
    start_time = time.time()

    try:
        await client.synthesize_speech(
            text=test_text,
            output_path=str(temp_output),
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Assertions
        assert temp_output.exists(), "Output file should exist"
        assert temp_output.stat().st_size > 0, "Output file should not be empty"

        # Read audio data for saving
        with open(temp_output, "rb") as f:
            audio_data = f.read()

        file_size = len(audio_data)

        # Save results
        request_data = {
            "endpoint": settings.HUME_AI_ENDPOINT,
            "voice": settings.HUME_AI_VOICE,
            "text": test_text,
            "format": "mp3",
        }

        save_test_result(
            results_dir=results_dir,
            test_name="hume_tts",
            request_data=request_data,
            response_data=audio_data,
            status="passed",
            duration_ms=duration_ms,
        )

        # Copy audio file to results with better name
        final_audio_path = results_dir / "hume_tts_response.mp3"
        shutil.copy(temp_output, final_audio_path)

        print(f"\n✅ Test passed - Results saved to: {results_dir}")
        print(f"   Text: {test_text}")
        print(f"   Audio file size: {file_size} bytes")
        print(f"   Duration: {duration_ms}ms")
        print(f"   Audio saved to: {final_audio_path}")

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        save_test_result(
            results_dir=results_dir,
            test_name="hume_tts",
            request_data={"error": str(e)},
            response_data=str(e),
            status="failed",
            duration_ms=duration_ms,
        )

        print(f"\n❌ Test failed - Error saved to: {results_dir}")
        raise
