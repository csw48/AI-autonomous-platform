"""Tests for database models and session"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.db.base import Base
from app.db.models import Document, DocumentChunk, Conversation, Message


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


@pytest.mark.asyncio
async def test_create_document(test_db_session):
    """Test creating a document"""
    document = Document(
        filename="test.pdf",
        content_type="application/pdf",
        file_size=1024,
        title="Test Document",
        status="pending"
    )

    test_db_session.add(document)
    await test_db_session.commit()

    # Verify
    result = await test_db_session.execute(select(Document))
    saved_doc = result.scalar_one()

    assert saved_doc.filename == "test.pdf"
    assert saved_doc.title == "Test Document"
    assert saved_doc.status == "pending"


@pytest.mark.asyncio
async def test_create_document_with_chunks(test_db_session):
    """Test creating document with chunks"""
    document = Document(
        filename="test.txt",
        content_type="text/plain",
        file_size=512,
    )

    chunk1 = DocumentChunk(
        content="This is chunk 1",
        chunk_index=0,
        token_count=5
    )

    chunk2 = DocumentChunk(
        content="This is chunk 2",
        chunk_index=1,
        token_count=5
    )

    document.chunks.append(chunk1)
    document.chunks.append(chunk2)

    test_db_session.add(document)
    await test_db_session.commit()

    # Verify
    result = await test_db_session.execute(select(Document))
    saved_doc = result.scalar_one()

    assert len(saved_doc.chunks) == 2
    assert saved_doc.chunks[0].content == "This is chunk 1"
    assert saved_doc.chunks[1].chunk_index == 1


@pytest.mark.asyncio
async def test_create_conversation(test_db_session):
    """Test creating a conversation"""
    conversation = Conversation(
        title="Test Conversation",
        session_id="test-session-123"
    )

    test_db_session.add(conversation)
    await test_db_session.commit()

    # Verify
    result = await test_db_session.execute(select(Conversation))
    saved_conv = result.scalar_one()

    assert saved_conv.title == "Test Conversation"
    assert saved_conv.session_id == "test-session-123"


@pytest.mark.asyncio
async def test_create_conversation_with_messages(test_db_session):
    """Test creating conversation with messages"""
    conversation = Conversation(
        title="Test Chat",
        session_id="session-456"
    )

    msg1 = Message(
        role="user",
        content="Hello!",
        tokens_used=2
    )

    msg2 = Message(
        role="assistant",
        content="Hi there!",
        tokens_used=3,
        model="gpt-4"
    )

    conversation.messages.append(msg1)
    conversation.messages.append(msg2)

    test_db_session.add(conversation)
    await test_db_session.commit()

    # Verify
    result = await test_db_session.execute(select(Conversation))
    saved_conv = result.scalar_one()

    assert len(saved_conv.messages) == 2
    assert saved_conv.messages[0].role == "user"
    assert saved_conv.messages[1].content == "Hi there!"


@pytest.mark.asyncio
async def test_cascade_delete_document(test_db_session):
    """Test cascade delete of document chunks"""
    document = Document(
        filename="test.pdf",
        content_type="application/pdf",
        file_size=1024
    )

    chunk = DocumentChunk(
        content="Test chunk",
        chunk_index=0
    )

    document.chunks.append(chunk)

    test_db_session.add(document)
    await test_db_session.commit()

    # Delete document
    await test_db_session.delete(document)
    await test_db_session.commit()

    # Verify chunks are also deleted
    result = await test_db_session.execute(select(DocumentChunk))
    chunks = result.scalars().all()

    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_document_metadata(test_db_session):
    """Test document metadata field"""
    document = Document(
        filename="test.pdf",
        content_type="application/pdf",
        file_size=1024,
        doc_metadata={"author": "John Doe", "pages": 10},
        tags=["important", "research"]
    )

    test_db_session.add(document)
    await test_db_session.commit()

    # Verify
    result = await test_db_session.execute(select(Document))
    saved_doc = result.scalar_one()

    assert saved_doc.doc_metadata["author"] == "John Doe"
    assert "important" in saved_doc.tags
