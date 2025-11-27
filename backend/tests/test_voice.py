"""Tests for voice API endpoints"""

import pytest
from httpx import AsyncClient
from app.main import app
import io


@pytest.mark.asyncio
async def test_voice_status():
    """Test voice service status endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/voice/status")

    assert response.status_code == 200
    data = response.json()

    assert "stt" in data
    assert "tts" in data
    assert data["stt"]["available"] is True
    assert data["stt"]["provider"] == "whisper"


@pytest.mark.asyncio
async def test_list_voices():
    """Test listing available TTS voices"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/voice/voices")

    assert response.status_code == 200
    data = response.json()

    assert "provider" in data
    assert "available" in data
    assert "voices" in data
    assert len(data["voices"]) > 0
    assert data["provider"] == "openai"


@pytest.mark.asyncio
async def test_transcribe_invalid_file_type():
    """Test transcription with invalid file type"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = await client.post("/api/v1/voice/transcribe", files=files)

    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tts_empty_text():
    """Test TTS with empty text"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/voice/synthesize",
            json={"text": ""}
        )

    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tts_text_too_long():
    """Test TTS with text exceeding limit"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        long_text = "a" * 5000  # Exceed 4096 character limit
        response = await client.post(
            "/api/v1/voice/synthesize",
            json={"text": long_text}
        )

    assert response.status_code == 400
    assert "too long" in response.json()["detail"]


# Note: Full STT/TTS tests would require actual audio files and API keys
# These are basic validation tests
