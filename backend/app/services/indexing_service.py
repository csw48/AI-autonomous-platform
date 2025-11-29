"""Document indexing service for vector database"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk
from app.services.text_extraction import TextExtractionService
from app.services.chunking import ChunkingService, TextChunk
from app.core.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing documents into vector database"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize indexing service

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
            embedding_model: Model to use for embeddings
        """
        self.text_extractor = TextExtractionService()
        self.chunker = ChunkingService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embeddings_service = EmbeddingsService()

    async def process_and_index_document(
        self,
        db: AsyncSession,
        document_id: int,
        file_content: bytes,
        content_type: str,
        language: Optional[str] = None,
        chunk_strategy: str = "sentence"
    ) -> Dict[str, Any]:
        """
        Process a document and index it into vector database

        Args:
            db: Database session
            document_id: ID of the document record
            file_content: File content as bytes
            content_type: MIME type of the file
            language: Language for OCR (optional)
            chunk_strategy: Chunking strategy ("sentence", "paragraph", "token")

        Returns:
            Dict with processing statistics

        Raises:
            Exception: If processing fails
        """
        try:
            # Get document record
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise Exception(f"Document with ID {document_id} not found")

            # Update status to processing
            document.status = "processing"
            await db.commit()

            logger.info(f"Starting to process document {document_id}: {document.filename}")

            # Step 1: Extract text
            try:
                extracted_text = await self.text_extractor.extract_text(
                    file_content=file_content,
                    content_type=content_type,
                    language=language
                )

                if not extracted_text or len(extracted_text.strip()) < 10:
                    raise Exception("Extracted text is too short or empty")

                logger.info(f"Extracted {len(extracted_text)} characters from document")

            except Exception as e:
                document.status = "failed"
                document.error_message = f"Text extraction failed: {str(e)}"
                await db.commit()
                raise

            # Step 2: Chunk text
            try:
                chunks = self.chunker.chunk_text(
                    text=extracted_text,
                    split_by=chunk_strategy,
                    metadata={
                        "document_id": document_id,
                        "filename": document.filename,
                        "content_type": content_type
                    }
                )

                logger.info(f"Created {len(chunks)} chunks from document")

            except Exception as e:
                document.status = "failed"
                document.error_message = f"Text chunking failed: {str(e)}"
                await db.commit()
                raise

            # Step 3: Generate embeddings
            try:
                chunk_texts = [chunk.content for chunk in chunks]
                logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")

                embeddings = await self.embeddings_service.generate_embeddings_batch(chunk_texts)

                logger.info(f"Successfully generated {len(embeddings)} embeddings")

                if len(embeddings) != len(chunks):
                    logger.warning(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)} chunks")

            except Exception as e:
                error_msg = f"Embedding generation failed: {str(e)}"
                logger.error(error_msg)
                document.status = "failed"
                document.error_message = error_msg
                await db.commit()
                raise Exception(error_msg)

            # Step 4: Save chunks to database
            try:
                for chunk, embedding in zip(chunks, embeddings):
                    db_chunk = DocumentChunk(
                        document_id=document_id,
                        content=chunk.content,
                        chunk_index=chunk.index,
                        embedding=embedding,
                        chunk_metadata={
                            "token_count": chunk.token_count,
                            "start_char": chunk.start_char,
                            "end_char": chunk.end_char,
                            **(chunk.metadata or {})
                        },
                        token_count=chunk.token_count
                    )
                    db.add(db_chunk)

                # Update document status
                document.status = "completed"
                document.updated_at = datetime.utcnow()

                await db.commit()

                logger.info(f"Successfully indexed document {document_id} with {len(chunks)} chunks")

                return {
                    "document_id": document_id,
                    "filename": document.filename,
                    "status": "completed",
                    "chunks_created": len(chunks),
                    "total_characters": len(extracted_text),
                    "total_tokens": sum(c.token_count for c in chunks)
                }

            except Exception as e:
                document.status = "failed"
                document.error_message = f"Database save failed: {str(e)}"
                await db.commit()
                raise

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            raise Exception(f"Document indexing failed: {str(e)}")

    async def reindex_document(
        self,
        db: AsyncSession,
        document_id: int
    ) -> Dict[str, Any]:
        """
        Re-index an existing document (delete old chunks and create new ones)

        Args:
            db: Database session
            document_id: ID of the document to re-index

        Returns:
            Dict with processing statistics
        """
        try:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise Exception(f"Document with ID {document_id} not found")

            # Delete existing chunks
            for chunk in document.chunks:
                await db.delete(chunk)

            await db.commit()

            logger.info(f"Deleted existing chunks for document {document_id}")

            # Re-process (need file content - this is a limitation)
            # In production, you should store file_path and read from storage
            raise NotImplementedError("Re-indexing requires access to original file content")

        except Exception as e:
            logger.error(f"Failed to re-index document {document_id}: {e}")
            raise

    async def get_indexing_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get statistics about indexed documents

        Args:
            db: Database session

        Returns:
            Dict with indexing statistics
        """
        try:
            # Count documents by status
            result = await db.execute(select(Document))
            documents = result.scalars().all()

            stats = {
                "total_documents": len(documents),
                "completed": sum(1 for d in documents if d.status == "completed"),
                "processing": sum(1 for d in documents if d.status == "processing"),
                "failed": sum(1 for d in documents if d.status == "failed"),
                "pending": sum(1 for d in documents if d.status == "pending")
            }

            # Count total chunks
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            stats["total_chunks"] = len(chunks)

            return stats

        except Exception as e:
            logger.error(f"Failed to get indexing stats: {e}")
            raise
