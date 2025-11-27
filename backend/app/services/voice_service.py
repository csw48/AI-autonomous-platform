"""Voice processing service with STT and TTS support"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, BinaryIO
import whisper
from openai import AsyncOpenAI
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
    """Text-to-Speech service using OpenAI TTS"""

    def __init__(self):
        self.provider = settings.tts_provider
        self.voice = settings.tts_voice

        if self.provider == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured for TTS")
                self.client = None
            else:
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info(f"Initialized OpenAI TTS with voice: {self.voice}")
        else:
            logger.warning(f"Unsupported TTS provider: {self.provider}")
            self.client = None

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: str = "tts-1"
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to convert to speech
            voice: Voice to use (default from settings)
            model: TTS model (tts-1 or tts-1-hd)

        Returns:
            Audio data as bytes (MP3 format)
        """
        if not self.client:
            raise RuntimeError("TTS client not initialized")

        voice = voice or self.voice

        try:
            logger.info(f"Synthesizing speech: {len(text)} chars with voice {voice}")

            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )

            # Get audio content
            audio_data = response.content

            logger.info(f"Speech synthesis completed: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if TTS service is available"""
        return self.client is not None


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
