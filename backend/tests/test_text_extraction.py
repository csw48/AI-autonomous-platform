"""Tests for text extraction service"""

import pytest
from io import BytesIO

from app.services.text_extraction import TextExtractionService


@pytest.mark.asyncio
async def test_extract_from_txt():
    """Test text extraction from plain text"""
    service = TextExtractionService()

    text_content = b"Hello, this is a test document.\nWith multiple lines."
    result = await service.extract_from_txt(text_content)

    assert "Hello" in result
    assert "test document" in result
    assert "multiple lines" in result


@pytest.mark.asyncio
async def test_extract_from_txt_different_encoding():
    """Test text extraction with different encoding"""
    service = TextExtractionService()

    text_content = "Příliš žluťoučký kůň".encode("utf-8")
    result = await service.extract_from_txt(text_content)

    assert "kůň" in result


@pytest.mark.asyncio
async def test_extract_text_unsupported_type():
    """Test extraction with unsupported content type"""
    service = TextExtractionService()

    with pytest.raises(Exception) as exc_info:
        await service.extract_text(b"test", "application/unknown")

    assert "Unsupported content type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_extract_text_dispatcher():
    """Test extract_text dispatcher for text files"""
    service = TextExtractionService()

    text_content = b"Test content"
    result = await service.extract_text(text_content, "text/plain")

    assert "Test content" in result
