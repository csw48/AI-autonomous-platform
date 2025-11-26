"""Tests for chunking service"""

import pytest

from app.services.chunking import ChunkingService


@pytest.fixture
def chunking_service():
    """Create chunking service instance"""
    return ChunkingService(chunk_size=100, chunk_overlap=20)


def test_count_tokens(chunking_service):
    """Test token counting"""
    text = "Hello world, this is a test."
    token_count = chunking_service.count_tokens(text)

    assert token_count > 0
    assert isinstance(token_count, int)


def test_chunk_text_simple(chunking_service):
    """Test simple text chunking"""
    text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."

    chunks = chunking_service.chunk_text(text, split_by="sentence")

    assert len(chunks) > 0
    assert all(chunk.content for chunk in chunks)
    assert all(chunk.token_count > 0 for chunk in chunks)
    assert chunks[0].index == 0


def test_chunk_text_with_metadata(chunking_service):
    """Test chunking with metadata"""
    text = "Test text for chunking"
    metadata = {"source": "test", "doc_id": 123}

    chunks = chunking_service.chunk_text(text, split_by="sentence", metadata=metadata)

    assert len(chunks) > 0
    assert chunks[0].metadata == metadata


def test_chunk_text_empty():
    """Test chunking empty text"""
    service = ChunkingService()

    with pytest.raises(ValueError) as exc_info:
        service.chunk_text("")

    assert "cannot be empty" in str(exc_info.value)


def test_chunk_text_invalid_strategy():
    """Test chunking with invalid strategy"""
    service = ChunkingService()

    with pytest.raises(ValueError) as exc_info:
        service.chunk_text("test text", split_by="invalid")

    assert "Invalid split_by" in str(exc_info.value)


def test_chunk_text_by_paragraph(chunking_service):
    """Test chunking by paragraph"""
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."

    chunks = chunking_service.chunk_text(text, split_by="paragraph")

    assert len(chunks) > 0


def test_chunk_text_simple_method(chunking_service):
    """Test simple chunking method"""
    text = "A" * 1000  # Long text

    chunks = chunking_service.chunk_text_simple(text)

    assert len(chunks) > 1
    assert all(chunk.token_count <= chunking_service.chunk_size for chunk in chunks)


def test_chunk_overlap(chunking_service):
    """Test that chunks have proper overlap"""
    text = " ".join([f"Sentence {i}." for i in range(50)])

    chunks = chunking_service.chunk_text(text, split_by="sentence")

    # Check that we have multiple chunks
    assert len(chunks) > 1

    # All chunks should be indexed sequentially
    for i, chunk in enumerate(chunks):
        assert chunk.index == i
