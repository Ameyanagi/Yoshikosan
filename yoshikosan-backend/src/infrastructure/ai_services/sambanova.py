"""SambaNova API client for multimodal inference."""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from src.config.settings import settings
from src.infrastructure.ai_services.utils import encode_image_to_base64

logger = logging.getLogger(__name__)


class SambanovaClient:
    """Client for SambaNova multimodal API."""

    def __init__(self) -> None:
        """Initialize SambaNova client with configuration from settings."""
        self.api_key = settings.SAMBANOVA_API_KEY
        self.model = settings.SAMBANOVA_MODEL
        self.endpoint = settings.SAMBANOVA_ENDPOINT
        self.whisper_model = settings.SAMBANOVA_WHISPER_MODEL
        self.whisper_endpoint = settings.SAMBANOVA_WHISPER_ENDPOINT

        if not self.api_key:
            logger.warning("SAMBANOVA_API_KEY not set - client will not work")

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """
        Analyze an image with a text prompt using SambaNova's multimodal model.

        Args:
            image_path: Path to the image file
            prompt: Text prompt to guide the analysis
            response_schema: Optional JSON schema for structured output.
                If provided, response will be parsed as JSON dict.
                Schema should follow JSON Schema Draft 7 format.

        Returns:
            str: Text response if no schema provided
            dict: Parsed JSON response if schema provided

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.TimeoutException: If request times out
            ValueError: If image encoding fails
        """
        # Encode image to base64
        try:
            base64_image = encode_image_to_base64(image_path)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            raise

        # Construct multimodal message
        message_content: list[dict[str, Any]] = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": base64_image},
            },
        ]

        # Build request payload
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": message_content,
                }
            ],
        }

        # Add JSON schema mode if requested
        if response_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": response_schema,
                },
            }
            # Ensure streaming is disabled for JSON mode
            payload["stream"] = False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"Sending multimodal request to SambaNova: "
            f"model={self.model}, schema={response_schema is not None}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Raw API response: {response_data}")

            # Extract content from response
            content = response_data["choices"][0]["message"]["content"]

            # Parse JSON if schema was provided
            if response_schema:
                try:
                    parsed = json.loads(content)
                    logger.info("Successfully parsed JSON response")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw content: {content}")
                    raise ValueError(f"Failed to parse JSON response: {e}") from e

            # Return text response
            logger.info(f"Received text response ({len(content)} chars)")
            return content

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from SambaNova API: {e.response.status_code} - {e.response.text}"
            )
            raise
        except httpx.TimeoutException:
            logger.error("Request to SambaNova API timed out")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling SambaNova API: {e}")
            raise

    async def chat_completion(
        self,
        message: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """
        Send a text-only message to SambaNova's chat model.

        Args:
            message: Text message/prompt
            response_schema: Optional JSON schema for structured output.
                If provided, response will be parsed as JSON dict.
                Schema should follow JSON Schema Draft 7 format.

        Returns:
            str: Text response if no schema provided
            dict: Parsed JSON response if schema provided

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.TimeoutException: If request times out
        """
        # Build request payload with text-only message
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": message,
                }
            ],
        }

        # Add JSON schema mode if requested
        if response_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": response_schema,
                },
            }
            # Ensure streaming is disabled for JSON mode
            payload["stream"] = False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"Sending text request to SambaNova: "
            f"model={self.model}, schema={response_schema is not None}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Raw API response: {response_data}")

            # Extract content from response
            content = response_data["choices"][0]["message"]["content"]

            # Parse JSON if schema was provided
            if response_schema:
                try:
                    parsed = json.loads(content)
                    logger.info("Successfully parsed JSON response")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw content: {content}")
                    raise ValueError(f"Failed to parse JSON response: {e}") from e

            # Return text response
            logger.info(f"Received text response ({len(content)} chars)")
            return content

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from SambaNova API: {e.response.status_code} - {e.response.text}"
            )
            raise
        except httpx.TimeoutException:
            logger.error("Request to SambaNova API timed out")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling SambaNova API: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> str:
        """
        Transcribe audio to text using SambaNova's Whisper model.

        Args:
            audio_path: Path to the audio file (mp3, wav, etc.)
            language: Optional language code (e.g., "ja" for Japanese, "en" for English)

        Returns:
            str: Transcribed text

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.TimeoutException: If request times out
            FileNotFoundError: If audio file doesn't exist
        """
        audio_file = Path(audio_path)

        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(
            f"Transcribing audio: {audio_file.name} "
            f"(model={self.whisper_model}, language={language})"
        )

        # Prepare multipart form data
        files = {
            "file": (audio_file.name, open(audio_file, "rb"), "audio/mpeg"),
        }

        data = {
            "model": self.whisper_model,
        }

        if language:
            data["language"] = language

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.whisper_endpoint,
                    files=files,
                    data=data,
                    headers=headers,
                )
                response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Raw Whisper API response: {response_data}")

            # Extract transcribed text
            text = response_data.get("text", "")
            logger.info(f"Transcription complete: {len(text)} chars")

            return text

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from SambaNova Whisper API: "
                f"{e.response.status_code} - {e.response.text}"
            )
            raise
        except httpx.TimeoutException:
            logger.error("Request to SambaNova Whisper API timed out")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling SambaNova Whisper API: {e}")
            raise
        finally:
            # Close the file
            if "file" in files:
                files["file"][1].close()
