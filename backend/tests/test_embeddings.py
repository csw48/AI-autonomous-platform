"""Tests for embeddings service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.embeddings import EmbeddingsService


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch("app.core.embeddings.AsyncOpenAI") as mock:
        client = MagicMock()

        # Mock embedding response
        embedding_data = MagicMock()
        embedding_data.embedding = [0.1] * 1536

        response = MagicMock()
        response.data = [embedding_data]

        client.embeddings.create = AsyncMock(return_value=response)
        mock.return_value = client

        yield mock


@pytest.mark.asyncio
async def test_generate_embedding(mock_openai_client):
    """Test generating single embedding"""
    service = EmbeddingsService(api_key="test-key")

    text = "This is a test document"
    embedding = await service.generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_generate_embedding_empty_text():
    """Test generating embedding with empty text"""
    service = EmbeddingsService(api_key="test-key")

    with pytest.raises(ValueError) as exc_info:
        await service.generate_embedding("")

    assert "cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_embedding_no_api_key():
    """Test generating embedding without API key"""
    service = EmbeddingsService(api_key="")

    with pytest.raises(Exception) as exc_info:
        await service.generate_embedding("test")

    assert "API key not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_embeddings_batch(mock_openai_client):
    """Test generating embeddings in batch"""
    # Mock multiple embeddings
    with patch("app.core.embeddings.AsyncOpenAI") as mock:
        client = MagicMock()

        # Mock 3 embedding responses
        embedding_data = [MagicMock(embedding=[0.1] * 1536) for _ in range(3)]
        response = MagicMock()
        response.data = embedding_data

        client.embeddings.create = AsyncMock(return_value=response)
        mock.return_value = client

        service = EmbeddingsService(api_key="test-key")
        texts = ["Text one", "Text two", "Text three"]
        embeddings = await service.generate_embeddings_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)


@pytest.mark.asyncio
async def test_generate_embeddings_empty_batch():
    """Test generating embeddings with empty batch"""
    service = EmbeddingsService(api_key="test-key")

    embeddings = await service.generate_embeddings_batch([])

    assert embeddings == []


@pytest.mark.asyncio
async def test_get_embedding_dimension():
    """Test getting embedding dimension"""
    service = EmbeddingsService(model="text-embedding-3-small")

    dimension = await service.get_embedding_dimension()

    assert dimension == 1536


def test_calculate_similarity():
    """Test cosine similarity calculation"""
    service = EmbeddingsService(api_key="test-key")

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


def test_calculate_similarity_different_dimensions():
    """Test similarity calculation with different dimensions"""
    service = EmbeddingsService(api_key="test-key")

    vec1 = [1.0, 2.0]
    vec2 = [1.0, 2.0, 3.0]

    with pytest.raises(ValueError) as exc_info:
        service.calculate_similarity(vec1, vec2)

    assert "same dimension" in str(exc_info.value)
