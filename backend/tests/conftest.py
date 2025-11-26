"""Pytest configuration and fixtures"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db


@pytest.fixture
def test_client():
    """Synchronous test client"""
    return TestClient(app)


@pytest.fixture
async def test_db_engine():
    """Create test database engine with SQLite"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session"""
    AsyncTestSession = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with AsyncTestSession() as session:
        yield session
        await session.rollback()


async def override_get_db(test_db_session):
    """Override get_db dependency for testing"""
    yield test_db_session


@pytest.fixture
async def async_client(test_db_session):
    """Asynchronous test client with test database"""
    # Override DB dependency
    async def get_test_db_override():
        yield test_db_session

    app.dependency_overrides[get_db] = get_test_db_override

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()
