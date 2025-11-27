"""Voice processing service with STT and TTS support"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, BinaryIO
import whisper
import soundfile as sf
import numpy as np

from ..core.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """Speech-to-Text service using OpenAI Whisper"""

    def __init__(self):
        self.model = None
        self.model_name = settings.whisper_model
        logger.info(f"Initializing Whisper model: {self.model_name}")

    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")

    async def transcribe(
        self,
        audio_file: BinaryIO,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio file to text

        Args:
            audio_file: Audio file binary content
            language: Optional language code (e.g., 'en', 'sk')

        Returns:
            dict with 'text' and 'language' keys
        """
        self._load_model()

        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_file.read())

        try:
            # Transcribe using Whisper
            logger.info(f"Transcribing audio file: {temp_path}")

            result = self.model.transcribe(
                temp_path,
                language=language,
                fp16=False  # Use FP32 for better CPU compatibility
            )

            transcription = {
                "text": result["text"].strip(),
                "language": result.get("language", language or "en")
            }

            logger.info(f"Transcription completed: {len(transcription['text'])} chars")
            return transcription

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TextToSpeechService:
    """Text-to-Speech service using gTTS (free Google TTS)"""

    def __init__(self):
        self.provider = settings.tts_provider
        self.voice = settings.tts_voice
        logger.info(f"Initialized gTTS (Google Text-to-Speech)")

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: str = "tts-1"  # Kept for API compatibility
    ) -> bytes:
        """
        Synthesize speech from text using gTTS

        Args:
            text: Text to convert to speech
            voice: Ignored (gTTS uses default voice)
            model: Ignored, kept for API compatibility

        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            from gtts import gTTS
            import io

            logger.info(f"Synthesizing speech: {len(text)} chars using gTTS")

            # Generate speech using gTTS
            tts = gTTS(text=text, lang='en', slow=False)

            # Save to BytesIO buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()

            logger.info(f"Speech synthesis completed: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if TTS service is available"""
        # gTTS is always available, no API key needed
        return True


class VoiceService:
    """Unified voice service for STT and TTS"""

    def __init__(self):
        self.stt = SpeechToTextService()
        self.tts = TextToSpeechService()
        logger.info("Voice service initialized")

    async def transcribe_audio(
        self,
        audio_file: BinaryIO,
        language: Optional[str] = None
    ) -> dict:
        """Transcribe audio to text"""
        return await self.stt.transcribe(audio_file, language)

    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> bytes:
        """Generate speech from text"""
        return await self.tts.synthesize(text, voice)

    def is_tts_available(self) -> bool:
        """Check if TTS is available"""
        return self.tts.is_available()


# Global voice service instance
voice_service = VoiceService()
