"""Tests for health check endpoint"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock


def test_health_check(test_client: TestClient):
    """Test health check endpoint returns correct status"""
    response = test_client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    # Status can be "ok" or "degraded" depending on DB availability
    assert data["status"] in ["ok", "degraded"]
    assert "version" in data
    assert "app_name" in data
    assert "services" in data
    assert isinstance(data["services"], dict)
    assert "database" in data["services"]


def test_root_endpoint(test_client: TestClient):
    """Test root endpoint"""
    response = test_client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check_async(async_client):
    """Test health check endpoint asynchronously"""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    # Status can be "ok" or "degraded" depending on DB availability
    assert data["status"] in ["ok", "degraded"]
    assert "version" in data
    assert "database" in data["services"]
