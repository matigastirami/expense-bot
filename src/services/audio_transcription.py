"""
Audio transcription service for converting voice messages to text.

This module provides transcription services using OpenAI's Whisper API
for processing voice messages in the Financial Analysis Agent.
"""

import logging
import os
import tempfile
from typing import Optional, TYPE_CHECKING
import aiofiles
import aiohttp

if TYPE_CHECKING:
    from aiogram.types import Voice

logger = logging.getLogger(__name__)


class AudioTranscriptionService:
    """Service for transcribing audio messages to text."""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the transcription service.

        Args:
            openai_api_key: OpenAI API key. If None, will try to get from environment.
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"

        if not self.api_key:
            logger.warning("⚠️ No OpenAI API key found. Audio transcription will not work.")
            logger.warning("   Set OPENAI_API_KEY environment variable to enable audio features.")

    async def transcribe_voice_message(self, voice_file_path: str, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe a voice message file to text.

        Args:
            voice_file_path: Path to the audio file
            language: Language hint for transcription (e.g., 'en', 'es')

        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.api_key:
            logger.error("❌ Cannot transcribe audio: No OpenAI API key configured")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                # Prepare the form data
                data = aiohttp.FormData()

                # Add the audio file
                async with aiofiles.open(voice_file_path, 'rb') as audio_file:
                    audio_content = await audio_file.read()
                    data.add_field('file', audio_content, filename='voice.ogg', content_type='audio/ogg')

                # Add model parameter
                data.add_field('model', 'whisper-1')

                # Add language hint if provided
                if language:
                    data.add_field('language', language)

                # Add response format
                data.add_field('response_format', 'text')

                # Prepare headers
                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }

                # Make the API request
                async with session.post(self.api_url, data=data, headers=headers) as response:
                    if response.status == 200:
                        transcription = await response.text()
                        transcription = transcription.strip()

                        if transcription:
                            logger.info(f"✅ Audio transcribed successfully: '{transcription[:50]}...'")
                            return transcription
                        else:
                            logger.warning("⚠️ Transcription was empty")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Transcription API error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error during audio transcription: {e}")
            return None

    async def download_and_transcribe_telegram_voice(self, bot, voice: "Voice", language: Optional[str] = None) -> Optional[str]:
        """
        Download a Telegram voice message and transcribe it.

        Args:
            bot: Telegram bot instance
            voice: Voice message object from Telegram
            language: Language hint for transcription

        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.api_key:
            return None

        temp_file = None
        try:
            # Get file info from Telegram
            file_info = await bot.get_file(voice.file_id)

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file_path = temp_file.name

            # Download the file
            await bot.download_file(file_info.file_path, temp_file_path)
            logger.info(f"📥 Downloaded voice message: {voice.duration}s, {voice.file_size} bytes")

            # Transcribe the audio
            transcription = await self.transcribe_voice_message(temp_file_path, language)

            return transcription

        except Exception as e:
            logger.error(f"❌ Error downloading/transcribing voice message: {e}")
            return None

        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug("🗑️ Cleaned up temporary audio file")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete temporary file: {e}")


# Global instance
audio_service = AudioTranscriptionService()
