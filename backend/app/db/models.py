"""Database models for AI platform"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base


class Document(Base):
    """Document model for storing uploaded documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=True)

    # Metadata
    title = Column(String(500), nullable=True)
    language = Column(String(10), nullable=True)
    tags = Column(JSON, nullable=True)
    doc_metadata = Column(JSON, nullable=True)

    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Document chunks for vector search"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    # Embedding (1536 dimensions for OpenAI text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=True)

    # Metadata
    chunk_metadata = Column(JSON, nullable=True)
    token_count = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    """Conversation history"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    # Conversation metadata
    title = Column(String(500), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Metadata
    msg_metadata = Column(JSON, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class VectorSearchCache(Base):
    """Cache for vector search results"""
    __tablename__ = "vector_search_cache"

    id = Column(Integer, primary_key=True, index=True)

    # Query
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536), nullable=True)

    # Results
    results = Column(JSON, nullable=False)
    result_count = Column(Integer, nullable=False)

    # Performance metrics
    search_time_ms = Column(Float, nullable=True)

    # Cache metadata
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
