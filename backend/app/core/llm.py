"""LLM wrapper with support for multiple providers"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
import tiktoken

from .config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        self.sync_client = OpenAI(api_key=api_key)

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using OpenAI API

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI API parameters

        Returns:
            Generated text
        """
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI returned empty content")
                return ""

            logger.info(
                f"LLM generation: {response.usage.prompt_tokens} prompt tokens, "
                f"{response.usage.completion_tokens} completion tokens"
            )

            return content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.tokenizer.encode(text))


class LLMManager:
    """Manages LLM providers and provides a unified interface"""

    def __init__(self):
        self.provider: Optional[BaseLLMProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize LLM provider based on settings"""
        provider = settings.llm_provider.lower()

        if provider == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured")
                return

            self.provider = OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.llm_model
            )
            logger.info(f"Initialized OpenAI provider with model {settings.llm_model}")

        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using configured LLM provider

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text

        Raises:
            RuntimeError: If no provider is configured
        """
        if not self.provider:
            raise RuntimeError("No LLM provider configured")

        return await self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.provider:
            raise RuntimeError("No LLM provider configured")

        return self.provider.count_tokens(text)

    def is_available(self) -> bool:
        """Check if LLM provider is available"""
        return self.provider is not None


# Global LLM manager instance
llm_manager = LLMManager()
