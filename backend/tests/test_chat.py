"""Tests for chat endpoint"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_chat_endpoint_not_available(test_client: TestClient):
    """Test chat endpoint when LLM is not available"""
    with patch("app.api.v1.chat.llm_manager") as mock_llm:
        mock_llm.is_available.return_value = False

        response = test_client.post(
            "/api/v1/chat",
            json={"message": "Hello, world!"}
        )

        assert response.status_code == 503
        assert "not available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_endpoint_success(async_client):
    """Test successful chat interaction"""
    with patch("app.api.v1.chat.llm_manager") as mock_llm:
        mock_llm.is_available.return_value = True
        mock_llm.generate = AsyncMock(return_value="This is a test response")
        mock_llm.count_tokens.return_value = 5

        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "Hello, world!"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["answer"] == "This is a test response"
        assert data["tokens_used"] == 5


@pytest.mark.asyncio
async def test_chat_endpoint_with_system_prompt(async_client):
    """Test chat with system prompt"""
    with patch("app.api.v1.chat.llm_manager") as mock_llm:
        mock_llm.is_available.return_value = True
        mock_llm.generate = AsyncMock(return_value="Response")
        mock_llm.count_tokens.return_value = 1

        response = await async_client.post(
            "/api/v1/chat",
            json={
                "message": "Hello!",
                "system_prompt": "You are a helpful assistant"
            }
        )

        assert response.status_code == 200
        mock_llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_chat_endpoint_with_temperature(async_client):
    """Test chat with custom temperature"""
    with patch("app.api.v1.chat.llm_manager") as mock_llm:
        mock_llm.is_available.return_value = True
        mock_llm.generate = AsyncMock(return_value="Response")
        mock_llm.count_tokens.return_value = 1

        response = await async_client.post(
            "/api/v1/chat",
            json={
                "message": "Hello!",
                "temperature": 0.9
            }
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_endpoint_with_max_tokens(async_client):
    """Test chat with max_tokens"""
    with patch("app.api.v1.chat.llm_manager") as mock_llm:
        mock_llm.is_available.return_value = True
        mock_llm.generate = AsyncMock(return_value="Response")
        mock_llm.count_tokens.return_value = 1

        response = await async_client.post(
            "/api/v1/chat",
            json={
                "message": "Hello!",
                "max_tokens": 100
            }
        )

        assert response.status_code == 200


def test_chat_endpoint_empty_message(test_client: TestClient):
    """Test chat with empty message"""
    response = test_client.post(
        "/api/v1/chat",
        json={"message": ""}
    )

    assert response.status_code == 422  # Validation error


def test_chat_endpoint_invalid_temperature(test_client: TestClient):
    """Test chat with invalid temperature"""
    response = test_client.post(
        "/api/v1/chat",
        json={
            "message": "Hello!",
            "temperature": 3.0  # Too high
        }
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_endpoint_generation_error(async_client):
    """Test chat when generation fails"""
    with patch("app.api.v1.chat.llm_manager") as mock_llm:
        mock_llm.is_available.return_value = True
        mock_llm.generate = AsyncMock(side_effect=Exception("API Error"))

        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "Hello!"}
        )

        assert response.status_code == 500
        assert "Failed to generate response" in response.json()["detail"]
