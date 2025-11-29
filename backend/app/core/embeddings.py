"""Embeddings generation service"""

import logging
from typing import List, Optional
import asyncio
from abc import ABC, abstractmethod
from functools import partial

from openai import AsyncOpenAI
import httpx
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(60.0, connect=10.0),
            max_retries=3
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings batch using OpenAI"""
        if not texts:
            return []

        batch_filtered = [t[:8000] if len(t) > 8000 else t for t in texts if t.strip()]

        if not batch_filtered:
            return [[0.0] * self.get_dimension()] * len(texts)

        response = await self.client.embeddings.create(
            model=self.model,
            input=batch_filtered,
            encoding_format="float"
        )
        return [item.embedding for item in response.data]

    def get_dimension(self) -> int:
        """Get OpenAI embedding dimension"""
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dimensions.get(self.model, 1536)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Gemini embedding provider"""

    def __init__(self, api_key: str, model: str = "models/embedding-001"):
        self.api_key = api_key
        self.model = model
        genai.configure(api_key=api_key)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Gemini handles long texts better, but still truncate very long ones
        max_chars = 20000
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")

        # Gemini embedding API is synchronous, run in executor for async
        loop = asyncio.get_event_loop()
        func = partial(
            genai.embed_content,
            model=self.model,
            content=text,
            task_type="retrieval_document"
        )

        # Run blocking call in thread executor with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await loop.run_in_executor(None, func)
                return result['embedding']
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Gemini embedding attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Gemini embedding failed after {max_retries} attempts: {e}")
                    raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings batch using Gemini"""
        if not texts:
            return []

        # Process texts individually for Gemini (it doesn't have batch API)
        embeddings = []
        for idx, text in enumerate(texts):
            if text and text.strip():
                try:
                    embedding = await self.generate_embedding(text)
                    embeddings.append(embedding)
                    logger.debug(f"Generated embedding {idx + 1}/{len(texts)}")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text {idx + 1}: {e}")
                    # Use zero vector as fallback
                    embeddings.append([0.0] * self.get_dimension())
            else:
                embeddings.append([0.0] * self.get_dimension())

            # Small delay to avoid rate limits (every 5 embeddings)
            if (idx + 1) % 5 == 0:
                await asyncio.sleep(0.2)

        return embeddings

    def get_dimension(self) -> int:
        """Get Gemini embedding dimension"""
        return 768  # Gemini embedding-001 produces 768-dimensional vectors


class EmbeddingsService:
    """Service for generating embeddings for text"""

    def __init__(self, batch_size: int = 100):
        """
        Initialize embeddings service

        Args:
            batch_size: Number of texts to process in one batch
        """
        self.batch_size = batch_size
        self.provider: Optional[BaseEmbeddingProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize embedding provider based on settings"""
        provider = settings.llm_provider.lower()

        if provider == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured")
                return

            self.provider = OpenAIEmbeddingProvider(
                api_key=settings.openai_api_key,
                model=settings.embedding_model
            )
            logger.info(f"Initialized OpenAI embedding provider with model {settings.embedding_model}")

        elif provider == "gemini":
            if not settings.gemini_api_key:
                logger.warning("Gemini API key not configured")
                return

            self.provider = GeminiEmbeddingProvider(
                api_key=settings.gemini_api_key,
                model=settings.embedding_model
            )
            logger.info(f"Initialized Gemini embedding provider with model {settings.embedding_model}")

        else:
            logger.error(f"Unsupported embedding provider: {provider}")
            raise ValueError(f"Unsupported embedding provider: {provider}")

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
        if not self.provider:
            raise RuntimeError("No embedding provider configured")

        try:
            embedding = await self.provider.generate_embedding(text)
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

        if not self.provider:
            raise RuntimeError("No embedding provider configured")

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                batch_embeddings = await self.provider.generate_embeddings_batch(batch)
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {i // self.batch_size + 1} ({len(batch)} texts)")

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
            Embedding dimension (e.g., 1536 for OpenAI, 768 for Gemini)
        """
        if not self.provider:
            raise RuntimeError("No embedding provider configured")

        return self.provider.get_dimension()

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


# Global instance
embeddings_service = EmbeddingsService()
