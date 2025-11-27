"""Voice API endpoints for STT and TTS"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import logging
import io

from ..services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger(__name__)


class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    text: str
    language: str


class TTSRequest(BaseModel):
    """Request model for text-to-speech"""
    text: str
    voice: Optional[str] = None
    model: str = "tts-1"


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Transcribe audio file to text using Whisper

    Args:
        file: Audio file (wav, mp3, m4a, etc.)
        language: Optional language code (e.g., 'en', 'sk')

    Returns:
        Transcription result with text and detected language
    """
    # Validate file type
    allowed_types = [
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/m4a",
        "audio/x-m4a",
        "audio/webm",
        "audio/ogg"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {file.content_type}. "
                   f"Supported: wav, mp3, m4a, webm, ogg"
        )

    try:
        logger.info(f"Transcribing audio: {file.filename} ({file.content_type})")

        # Read file content
        content = await file.read()
        audio_file = io.BytesIO(content)

        # Transcribe
        result = await voice_service.transcribe_audio(audio_file, language)

        return TranscriptionResponse(
            text=result["text"],
            language=result["language"]
        )

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using OpenAI TTS

    Args:
        request: TTS request with text and voice parameters

    Returns:
        Audio file (MP3 format)
    """
    # Validate input first
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(request.text) > 4096:
        raise HTTPException(
            status_code=400,
            detail="Text too long. Maximum 4096 characters."
        )

    # Then check service availability
    if not voice_service.is_tts_available():
        raise HTTPException(
            status_code=503,
            detail="TTS service not available. Check OpenAI API key configuration."
        )

    try:
        logger.info(f"Synthesizing speech: {len(request.text)} chars")

        # Generate speech
        audio_data = await voice_service.generate_speech(
            text=request.text,
            voice=request.voice
        )

        # Return as streaming audio
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/voices")
async def list_voices():
    """
    List available TTS voices

    Returns:
        List of available voices
    """
    # OpenAI TTS voices
    voices = [
        {"id": "alloy", "name": "Alloy", "description": "Neutral and balanced"},
        {"id": "echo", "name": "Echo", "description": "Clear and articulate"},
        {"id": "fable", "name": "Fable", "description": "Warm and engaging"},
        {"id": "onyx", "name": "Onyx", "description": "Deep and authoritative"},
        {"id": "nova", "name": "Nova", "description": "Energetic and dynamic"},
        {"id": "shimmer", "name": "Shimmer", "description": "Soft and gentle"}
    ]

    return {
        "provider": "openai",
        "available": voice_service.is_tts_available(),
        "voices": voices
    }


@router.get("/status")
async def voice_status():
    """
    Get voice service status

    Returns:
        Service availability status
    """
    return {
        "stt": {
            "available": True,
            "provider": "whisper",
            "model": voice_service.stt.model_name
        },
        "tts": {
            "available": voice_service.is_tts_available(),
            "provider": voice_service.tts.provider,
            "voice": voice_service.tts.voice
        }
    }
