"""Tests for documents API endpoints"""

import pytest
from io import BytesIO
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_upload_document_txt():
    """Test uploading a text document"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test file
        file_content = b"This is a test document with some content."

        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", file_content, "text/plain")},
            data={
                "title": "Test Document",
                "language": "en",
                "tags": "test,sample",
                "chunk_strategy": "sentence"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "document_id" in data
        assert data["filename"] == "test.txt"
        assert data["status"] in ["pending", "processing"]


@pytest.mark.asyncio
async def test_upload_document_unsupported_type():
    """Test uploading unsupported file type"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.xyz", b"content", "application/unknown")},
            data={"title": "Test"}
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_document_empty_file():
    """Test uploading empty file"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"", "text/plain")},
            data={"title": "Test"}
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_document_status():
    """Test getting document status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First upload a document
        file_content = b"Test content"
        upload_response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", file_content, "text/plain")},
            data={"title": "Test"}
        )

        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        # Get status
        status_response = await client.get(f"/api/v1/documents/{document_id}")

        assert status_response.status_code == 200
        data = status_response.json()

        assert data["document_id"] == document_id
        assert data["filename"] == "test.txt"
        assert "status" in data


@pytest.mark.asyncio
async def test_get_document_not_found():
    """Test getting status of non-existent document"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/documents/99999")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_documents():
    """Test listing documents"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/documents/")

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)


@pytest.mark.asyncio
async def test_delete_document():
    """Test deleting a document"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First upload a document
        file_content = b"Test content"
        upload_response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", file_content, "text/plain")},
            data={"title": "Test"}
        )

        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        # Delete it
        delete_response = await client.delete(f"/api/v1/documents/{document_id}")

        assert delete_response.status_code == 200

        # Verify it's gone
        get_response = await client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_indexing_stats():
    """Test getting indexing statistics"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/documents/stats/indexing")

        assert response.status_code == 200
        data = response.json()

        assert "total_documents" in data
        assert "completed" in data
        assert "processing" in data
        assert "failed" in data
        assert "pending" in data
        assert "total_chunks" in data
