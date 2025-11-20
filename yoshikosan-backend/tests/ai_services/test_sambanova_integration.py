"""Integration tests for SambaNova API client."""

import time
from pathlib import Path

import pytest

from src.config.settings import settings
from src.infrastructure.ai_services.sambanova import SambanovaClient
from tests.ai_services.conftest import save_test_result


@pytest.mark.asyncio
async def test_sambanova_analyze_image_text(
    lego_image_path: str, results_dir: Path
) -> None:
    """Test SambaNova image analysis with text response."""
    # Skip if API key not configured
    if not settings.SAMBANOVA_API_KEY:
        pytest.skip("SAMBANOVA_API_KEY not set in environment")

    # Verify test image exists
    if not Path(lego_image_path).exists():
        pytest.skip(f"Test image not found: {lego_image_path}")

    client = SambanovaClient()
    prompt = "What do you see in this image? Describe it in detail."

    # Measure execution time
    start_time = time.time()

    try:
        response = await client.analyze_image(
            image_path=lego_image_path,
            prompt=prompt,
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Assertions
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"

        # Save results
        request_data = {
            "endpoint": settings.SAMBANOVA_ENDPOINT,
            "model": settings.SAMBANOVA_MODEL,
            "prompt": prompt,
            "image": lego_image_path,
            "response_schema": None,
        }

        save_test_result(
            results_dir=results_dir,
            test_name="sambanova_text",
            request_data=request_data,
            response_data=response,
            status="passed",
            duration_ms=duration_ms,
        )

        print(f"\n✅ Test passed - Results saved to: {results_dir}")
        print(f"   Response length: {len(response)} chars")
        print(f"   Duration: {duration_ms}ms")

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        save_test_result(
            results_dir=results_dir,
            test_name="sambanova_text",
            request_data={"error": str(e)},
            response_data=str(e),
            status="failed",
            duration_ms=duration_ms,
        )

        print(f"\n❌ Test failed - Error saved to: {results_dir}")
        raise


@pytest.mark.asyncio
async def test_sambanova_analyze_image_json_schema(
    lego_image_path: str, results_dir: Path
) -> None:
    """Test SambaNova image analysis with JSON schema response."""
    # Skip if API key not configured
    if not settings.SAMBANOVA_API_KEY:
        pytest.skip("SAMBANOVA_API_KEY not set in environment")

    # Verify test image exists
    if not Path(lego_image_path).exists():
        pytest.skip(f"Test image not found: {lego_image_path}")

    client = SambanovaClient()
    prompt = "Analyze this image and determine if it contains LEGO bricks. Provide a description."

    # Define JSON schema
    schema = {
        "type": "object",
        "properties": {
            "has_lego": {"type": "boolean"},
            "description": {"type": "string"},
        },
        "required": ["has_lego", "description"],
        "additionalProperties": False,
    }

    # Measure execution time
    start_time = time.time()

    try:
        response = await client.analyze_image(
            image_path=lego_image_path,
            prompt=prompt,
            response_schema=schema,
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Assertions
        assert isinstance(response, dict), "Response should be a dict"
        assert "has_lego" in response, "Response should have 'has_lego' key"
        assert "description" in response, "Response should have 'description' key"
        assert isinstance(response["has_lego"], bool), "'has_lego' should be boolean"
        assert isinstance(response["description"], str), (
            "'description' should be string"
        )

        # Save results
        request_data = {
            "endpoint": settings.SAMBANOVA_ENDPOINT,
            "model": settings.SAMBANOVA_MODEL,
            "prompt": prompt,
            "image": lego_image_path,
            "response_schema": schema,
        }

        save_test_result(
            results_dir=results_dir,
            test_name="sambanova_json",
            request_data=request_data,
            response_data=response,
            status="passed",
            duration_ms=duration_ms,
        )

        print(f"\n✅ Test passed - Results saved to: {results_dir}")
        print(f"   has_lego: {response['has_lego']}")
        print(f"   Description: {response['description'][:100]}...")
        print(f"   Duration: {duration_ms}ms")

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        save_test_result(
            results_dir=results_dir,
            test_name="sambanova_json",
            request_data={"error": str(e)},
            response_data=str(e),
            status="failed",
            duration_ms=duration_ms,
        )

        print(f"\n❌ Test failed - Error saved to: {results_dir}")
        raise


@pytest.mark.asyncio
async def test_sambanova_transcribe_audio_whisper(results_dir: Path) -> None:
    """Test SambaNova Whisper audio transcription."""
    # Skip if API key not configured
    if not settings.SAMBANOVA_API_KEY:
        pytest.skip("SAMBANOVA_API_KEY not set in environment")

    # Path to the Hume AI generated audio
    audio_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "sound"
        / "konnichiwa_hume.mp3"
    )

    # Skip if audio file doesn't exist
    if not audio_path.exists():
        pytest.skip(f"Test audio not found: {audio_path}")

    client = SambanovaClient()

    # Measure execution time
    start_time = time.time()

    try:
        transcription = await client.transcribe_audio(
            audio_path=str(audio_path),
            language="ja",  # Japanese
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Assertions
        assert isinstance(transcription, str), "Transcription should be a string"
        assert len(transcription) > 0, "Transcription should not be empty"

        # Save results
        request_data = {
            "endpoint": settings.SAMBANOVA_WHISPER_ENDPOINT,
            "model": settings.SAMBANOVA_WHISPER_MODEL,
            "audio_file": str(audio_path),
            "language": "ja",
        }

        save_test_result(
            results_dir=results_dir,
            test_name="sambanova_whisper",
            request_data=request_data,
            response_data=transcription,
            status="passed",
            duration_ms=duration_ms,
        )

        print(f"\n✅ Test passed - Results saved to: {results_dir}")
        print(f"   Audio: {audio_path.name}")
        print(f"   Transcription: {transcription}")
        print(f"   Duration: {duration_ms}ms")

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        save_test_result(
            results_dir=results_dir,
            test_name="sambanova_whisper",
            request_data={"error": str(e)},
            response_data=str(e),
            status="failed",
            duration_ms=duration_ms,
        )

        print(f"\n❌ Test failed - Error saved to: {results_dir}")
        raise
