"""Document upload and management endpoints"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models import Document, DocumentChunk
from app.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


# Schemas
class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    document_id: int
    filename: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    """Response for document status"""
    document_id: int
    filename: str
    status: str
    error_message: Optional[str] = None
    chunks_count: int
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Response for document list"""
    documents: List[DocumentStatusResponse]
    total: int


class IndexingStatsResponse(BaseModel):
    """Response for indexing statistics"""
    total_documents: int
    completed: int
    processing: int
    failed: int
    pending: int
    total_chunks: int


# Supported file types
SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "application/msword",  # DOC
    "text/plain",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/bmp"
}


async def process_document_background(
    document_id: int,
    file_content: bytes,
    content_type: str,
    language: Optional[str],
    chunk_strategy: str
):
    """Background task to process and index document"""
    from app.db.session import async_session_maker

    indexing_service = IndexingService()

    try:
        # Create a new database session for background task
        async with async_session_maker() as db:
            await indexing_service.process_and_index_document(
                db=db,
                document_id=document_id,
                file_content=file_content,
                content_type=content_type,
                language=language,
                chunk_strategy=chunk_strategy
            )
        logger.info(f"Background processing completed for document {document_id}")
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
    tags: Optional[str] = Form(None),
    chunk_strategy: str = Form("sentence"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and index a document

    Args:
        file: The file to upload
        title: Optional title for the document
        language: Language for OCR (default: en)
        tags: Comma-separated tags
        chunk_strategy: Chunking strategy (sentence, paragraph, token)
        db: Database session

    Returns:
        DocumentUploadResponse with document ID and status

    Raises:
        HTTPException: If upload fails or file type not supported
    """
    try:
        # Validate file type
        if file.content_type not in SUPPORTED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(SUPPORTED_CONTENT_TYPES)}"
            )

        # Validate chunk strategy
        if chunk_strategy not in ["sentence", "paragraph", "token"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid chunk_strategy. Must be: sentence, paragraph, or token"
            )

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Create document record
        document = Document(
            filename=file.filename,
            content_type=file.content_type,
            file_size=file_size,
            title=title or file.filename,
            language=language,
            tags=tag_list,
            status="pending"
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        logger.info(f"Created document record {document.id}: {file.filename}")

        # Schedule background processing
        background_tasks.add_task(
            process_document_background,
            document_id=document.id,
            file_content=file_content,
            content_type=file.content_type,
            language=language,
            chunk_strategy=chunk_strategy
        )

        return DocumentUploadResponse(
            document_id=document.id,
            filename=file.filename,
            status="pending",
            message="Document uploaded successfully. Processing started in background."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document processing status

    Args:
        document_id: ID of the document
        db: Database session

    Returns:
        DocumentStatusResponse with document details

    Raises:
        HTTPException: If document not found
    """
    try:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )

        chunks_count = len(document.chunks)

        return DocumentStatusResponse(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
            error_message=document.error_message,
            chunks_count=chunks_count,
            created_at=document.created_at,
            updated_at=document.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents

    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        status: Filter by status (optional)
        db: Database session

    Returns:
        DocumentListResponse with list of documents

    Raises:
        HTTPException: If query fails
    """
    try:
        query = select(Document)

        if status:
            query = query.where(Document.status == status)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        documents = result.scalars().all()

        # Get total count
        count_query = select(func.count()).select_from(Document)
        if status:
            count_query = count_query.where(Document.status == status)
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get chunk counts for each document
        document_responses = []
        for doc in documents:
            chunk_count_query = select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            chunk_count_result = await db.execute(chunk_count_query)
            chunks_count = chunk_count_result.scalar()

            document_responses.append(
                DocumentStatusResponse(
                    document_id=doc.id,
                    filename=doc.filename,
                    status=doc.status,
                    error_message=doc.error_message,
                    chunks_count=chunks_count,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at
                )
            )

        return DocumentListResponse(
            documents=document_responses,
            total=total
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and its chunks

    Args:
        document_id: ID of the document to delete
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )

        await db.delete(document)
        await db.commit()

        logger.info(f"Deleted document {document_id}: {document.filename}")

        return {"message": f"Document {document_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats/indexing", response_model=IndexingStatsResponse)
async def get_indexing_stats(db: AsyncSession = Depends(get_db)):
    """
    Get indexing statistics

    Args:
        db: Database session

    Returns:
        IndexingStatsResponse with statistics

    Raises:
        HTTPException: If query fails
    """
    try:
        indexing_service = IndexingService()
        stats = await indexing_service.get_indexing_stats(db)

        return IndexingStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get indexing stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get indexing stats: {str(e)}"
        )
