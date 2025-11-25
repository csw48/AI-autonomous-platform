"""Pytest configuration and fixtures"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client():
    """Synchronous test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Asynchronous test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
