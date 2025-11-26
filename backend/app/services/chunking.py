"""Text chunking service for document processing"""

import logging
import re
from typing import List, Optional
from dataclasses import dataclass

import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    index: int
    token_count: int
    start_char: int
    end_char: int
    metadata: Optional[dict] = None


class ChunkingService:
    """Service for chunking text into smaller pieces for embedding"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        model_name: str = "gpt-4"
    ):
        """
        Initialize chunking service

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
            model_name: Model name for tokenization
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name

        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning(f"Model {model_name} not found, using cl100k_base encoding")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count tokens

        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))

    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitter - can be improved with spaCy or nltk
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]

    def chunk_text(
        self,
        text: str,
        split_by: str = "sentence",
        metadata: Optional[dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text into smaller pieces

        Args:
            text: Text to chunk
            split_by: Splitting strategy ("sentence", "paragraph", "token")
            metadata: Additional metadata to attach to chunks

        Returns:
            List of TextChunk objects

        Raises:
            ValueError: If text is empty or split_by is invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if split_by not in ["sentence", "paragraph", "token"]:
            raise ValueError(f"Invalid split_by value: {split_by}")

        logger.info(f"Chunking text of {len(text)} characters using {split_by} strategy")

        chunks = []

        if split_by == "paragraph":
            segments = self._split_by_paragraphs(text)
        elif split_by == "sentence":
            segments = self._split_by_sentences(text)
        else:  # token-based chunking
            segments = [text]

        current_chunk = []
        current_tokens = 0
        current_start_char = 0
        chunk_index = 0

        for segment in segments:
            segment_tokens = self.count_tokens(segment)

            # If single segment exceeds chunk_size, split it further
            if segment_tokens > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(TextChunk(
                        content=chunk_text,
                        index=chunk_index,
                        token_count=current_tokens,
                        start_char=current_start_char,
                        end_char=current_start_char + len(chunk_text),
                        metadata=metadata
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0

                # Split large segment by tokens
                tokens = self.tokenizer.encode(segment)
                for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
                    chunk_tokens = tokens[i:i + self.chunk_size]
                    chunk_text = self.tokenizer.decode(chunk_tokens)

                    chunks.append(TextChunk(
                        content=chunk_text,
                        index=chunk_index,
                        token_count=len(chunk_tokens),
                        start_char=current_start_char,
                        end_char=current_start_char + len(chunk_text),
                        metadata=metadata
                    ))
                    chunk_index += 1
                    current_start_char += len(chunk_text)

                continue

            # Add segment to current chunk if it fits
            if current_tokens + segment_tokens <= self.chunk_size:
                current_chunk.append(segment)
                current_tokens += segment_tokens
            else:
                # Save current chunk
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(TextChunk(
                        content=chunk_text,
                        index=chunk_index,
                        token_count=current_tokens,
                        start_char=current_start_char,
                        end_char=current_start_char + len(chunk_text),
                        metadata=metadata
                    ))
                    chunk_index += 1

                    # Keep overlap
                    if self.chunk_overlap > 0 and len(current_chunk) > 1:
                        overlap_text = current_chunk[-1]
                        overlap_tokens = self.count_tokens(overlap_text)
                        current_chunk = [overlap_text]
                        current_tokens = overlap_tokens
                        current_start_char += len(chunk_text) - len(overlap_text)
                    else:
                        current_chunk = []
                        current_tokens = 0
                        current_start_char += len(chunk_text)

                # Add new segment
                current_chunk.append(segment)
                current_tokens += segment_tokens

        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(TextChunk(
                content=chunk_text,
                index=chunk_index,
                token_count=current_tokens,
                start_char=current_start_char,
                end_char=current_start_char + len(chunk_text),
                metadata=metadata
            ))

        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

    def chunk_text_simple(self, text: str, metadata: Optional[dict] = None) -> List[TextChunk]:
        """
        Simple chunking by token count without preserving sentence boundaries

        Args:
            text: Text to chunk
            metadata: Additional metadata

        Returns:
            List of TextChunk objects
        """
        tokens = self.tokenizer.encode(text)
        chunks = []

        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append(TextChunk(
                content=chunk_text,
                index=i // (self.chunk_size - self.chunk_overlap),
                token_count=len(chunk_tokens),
                start_char=0,  # Not tracked in simple mode
                end_char=0,
                metadata=metadata
            ))

        logger.info(f"Created {len(chunks)} simple chunks from {len(tokens)} tokens")
        return chunks
