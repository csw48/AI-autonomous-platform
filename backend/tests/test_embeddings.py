"""Tests for embeddings service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from app.core.embeddings import EmbeddingsService, GeminiEmbeddingProvider, OpenAIEmbeddingProvider


@pytest.fixture
def mock_settings_gemini():
    """Mock settings for Gemini provider"""
    with patch("app.core.embeddings.settings") as mock_settings:
        mock_settings.llm_provider = "gemini"
        mock_settings.gemini_api_key = "test-gemini-key"
        mock_settings.embedding_model = "models/embedding-001"
        yield mock_settings


@pytest.fixture
def mock_settings_openai():
    """Mock settings for OpenAI provider"""
    with patch("app.core.embeddings.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.embedding_model = "text-embedding-3-small"
        yield mock_settings


@pytest.mark.asyncio
async def test_generate_embedding_gemini(mock_settings_gemini):
    """Test generating single embedding with Gemini"""
    with patch("app.core.embeddings.genai.embed_content") as mock_embed:
        mock_embed.return_value = {"embedding": [0.1] * 768}

        service = EmbeddingsService()
        text = "This is a test document"
        embedding = await service.generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_generate_embedding_empty_text(mock_settings_gemini):
    """Test generating embedding with empty text"""
    service = EmbeddingsService()

    with pytest.raises(Exception) as exc_info:
        await service.generate_embedding("")

    assert "cannot be empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_gemini(mock_settings_gemini):
    """Test generating embeddings in batch with Gemini"""
    with patch("app.core.embeddings.genai.embed_content") as mock_embed:
        mock_embed.return_value = {"embedding": [0.1] * 768}

        service = EmbeddingsService()
        texts = ["Text one", "Text two", "Text three"]
        embeddings = await service.generate_embeddings_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)


@pytest.mark.asyncio
async def test_generate_embeddings_empty_batch(mock_settings_gemini):
    """Test generating embeddings with empty batch"""
    service = EmbeddingsService()

    embeddings = await service.generate_embeddings_batch([])

    assert embeddings == []


@pytest.mark.asyncio
async def test_get_embedding_dimension_gemini(mock_settings_gemini):
    """Test getting embedding dimension for Gemini"""
    service = EmbeddingsService()

    dimension = await service.get_embedding_dimension()

    assert dimension == 768


@pytest.mark.asyncio
async def test_get_embedding_dimension_openai(mock_settings_openai):
    """Test getting embedding dimension for OpenAI"""
    with patch("app.core.embeddings.AsyncOpenAI"):
        service = EmbeddingsService()
        dimension = await service.get_embedding_dimension()
        assert dimension == 1536


def test_calculate_similarity(mock_settings_gemini):
    """Test cosine similarity calculation"""
    service = EmbeddingsService()

    # Identical vectors
    vec1 = [1.0, 2.0, 3.0]
    vec2 = [1.0, 2.0, 3.0]
    similarity = service.calculate_similarity(vec1, vec2)

    assert abs(similarity - 1.0) < 0.001

    # Orthogonal vectors
    vec3 = [1.0, 0.0]
    vec4 = [0.0, 1.0]
    similarity = service.calculate_similarity(vec3, vec4)

    assert abs(similarity - 0.0) < 0.001


def test_calculate_similarity_different_dimensions(mock_settings_gemini):
    """Test similarity calculation with different dimensions"""
    service = EmbeddingsService()

    vec1 = [1.0, 2.0]
    vec2 = [1.0, 2.0, 3.0]

    with pytest.raises(ValueError) as exc_info:
        service.calculate_similarity(vec1, vec2)

    assert "same dimension" in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_provider():
    """Test OpenAI provider directly"""
    with patch("app.core.embeddings.AsyncOpenAI") as mock_client_class:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        provider = OpenAIEmbeddingProvider("test-key", "text-embedding-3-small")
        embedding = await provider.generate_embedding("test text")

        assert len(embedding) == 1536
        assert provider.get_dimension() == 1536


@pytest.mark.asyncio
async def test_gemini_provider():
    """Test Gemini provider directly"""
    with patch("app.core.embeddings.genai") as mock_genai:
        mock_genai.embed_content.return_value = {"embedding": [0.1] * 768}

        provider = GeminiEmbeddingProvider("test-key", "models/embedding-001")
        embedding = await provider.generate_embedding("test text")

        assert len(embedding) == 768
        assert provider.get_dimension() == 768
