"""Database models for AI platform"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
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


class Workflow(Base):
    """Workflow definition model"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)

    # Workflow metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Workflow configuration
    steps = Column(JSON, nullable=False)  # List of workflow steps with actions
    variables = Column(JSON, nullable=True)  # Default variables for the workflow

    # Workflow state
    enabled = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Ownership
    created_by = Column(String(255), nullable=True)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    template = relationship("WorkflowTemplate", back_populates="workflows")


class WorkflowExecution(Base):
    """Workflow execution instance"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Execution state
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, running, completed, failed, cancelled
    current_step = Column(Integer, default=0, nullable=False)

    # Execution data
    input_data = Column(JSON, nullable=True)  # Input variables for this execution
    output_data = Column(JSON, nullable=True)  # Final output of the workflow
    context = Column(JSON, nullable=True)  # Runtime context and variables

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_step = Column(Integer, nullable=True)

    # Performance metrics
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    step_executions = relationship("WorkflowStepExecution", back_populates="execution", cascade="all, delete-orphan")


class WorkflowStepExecution(Base):
    """Individual workflow step execution"""
    __tablename__ = "workflow_step_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Step identification
    step_index = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=True)
    action_type = Column(String(100), nullable=False)  # llm_query, doc_search, notion_update, http_request, data_transform

    # Step state
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed, skipped

    # Step data
    input_data = Column(JSON, nullable=True)  # Input to this step
    output_data = Column(JSON, nullable=True)  # Output from this step
    parameters = Column(JSON, nullable=True)  # Step configuration

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Performance metrics
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="step_executions")


class WorkflowTemplate(Base):
    """Pre-built workflow templates"""
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # data_processing, content_generation, automation, etc.

    # Template configuration
    steps = Column(JSON, nullable=False)  # Template workflow steps
    default_variables = Column(JSON, nullable=True)  # Default variable values
    required_variables = Column(JSON, nullable=True)  # List of required variable names

    # Template state
    is_public = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)

    # Metadata
    tags = Column(JSON, nullable=True)  # Tags for discovery
    author = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workflows = relationship("Workflow", back_populates="template")
