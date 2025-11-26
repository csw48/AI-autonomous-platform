"""Embeddings generation service"""

import logging
from typing import List, Optional
import asyncio

from openai import AsyncOpenAI
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating embeddings for text"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        max_retries: int = 3
    ):
        """
        Initialize embeddings service

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model to use
            batch_size: Number of texts to process in one batch
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries

        if not self.api_key:
            logger.warning("OpenAI API key not provided - embeddings will fail")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=httpx.Timeout(60.0, connect=10.0),
            max_retries=max_retries
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        try:
            # Truncate text if too long (OpenAI has token limits)
            max_chars = 8000
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters for embedding")

            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise Exception(f"Embedding generation failed: {str(e)}")

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        if not texts:
            return []

        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                # Filter empty texts
                batch_filtered = [t[:8000] if len(t) > 8000 else t for t in batch if t.strip()]

                if not batch_filtered:
                    logger.warning(f"Batch {i // self.batch_size} has no valid texts")
                    all_embeddings.extend([[0.0] * 1536] * len(batch))  # Return zero vectors
                    continue

                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch_filtered,
                    encoding_format="float"
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {i // self.batch_size + 1} ({len(batch_filtered)} texts)")

                # Small delay to avoid rate limits
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i // self.batch_size}: {e}")
                raise Exception(f"Batch embedding generation failed: {str(e)}")

        logger.info(f"Generated {len(all_embeddings)} embeddings total")
        return all_embeddings

    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model

        Returns:
            Embedding dimension (e.g., 1536 for text-embedding-3-small)
        """
        # Model dimension mapping
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

        return model_dimensions.get(self.model, 1536)

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (-1 to 1)
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)
        return similarity

    async def close(self):
        """Close the async client"""
        await self.client.close()


# Global instance
embeddings_service = EmbeddingsService()
