"""Hume AI client for empathic text-to-speech."""

import base64
import logging
from pathlib import Path

from hume import AsyncHumeClient

from src.config.settings import settings

logger = logging.getLogger(__name__)


class HumeClient:
    """Client for Hume AI empathic TTS API."""

    def __init__(self) -> None:
        """Initialize Hume AI client with configuration from settings."""
        self.api_key = settings.HUME_AI_API_KEY
        self.voice_id = settings.HUME_AI_VOICE

        if not self.api_key:
            logger.warning("HUME_AI_API_KEY not set - client will not work")

    async def synthesize_speech(
        self,
        text: str,
        output_path: str,
    ) -> None:
        """
        Synthesize speech from text using Hume AI's empathic TTS.

        Args:
            text: Text to synthesize (supports Japanese)
            output_path: Path where MP3 file will be saved

        Raises:
            Exception: If API call fails or file writing fails
        """
        logger.info(
            f"Requesting TTS from Hume AI: text_length={len(text)}, voice={self.voice_id}"
        )

        try:
            # Initialize Hume client
            client = AsyncHumeClient(api_key=self.api_key)

            # Create utterance with voice ID as dict
            utterances = [
                {
                    "text": text,
                    "voice": {"id": self.voice_id},
                }
            ]

            # Synthesize speech
            result = await client.tts.synthesize_json(
                utterances=utterances,
            )

            # Extract audio data from first generation
            if not result or not result.generations or len(result.generations) == 0:
                raise ValueError("No audio data returned from Hume AI")

            audio_base64 = result.generations[0].audio

            # Decode base64 audio and save to file
            audio_bytes = base64.b64decode(audio_base64)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "wb") as f:
                f.write(audio_bytes)

            file_size = len(audio_bytes)
            logger.info(
                f"Successfully saved TTS audio to {output_path} ({file_size} bytes)"
            )

        except Exception as e:
            logger.error(f"Error calling Hume AI API: {e}")
            raise
