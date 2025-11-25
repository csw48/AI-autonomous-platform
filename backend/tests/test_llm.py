"""Tests for LLM module"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice, CompletionUsage

from app.core.llm import OpenAIProvider, LLMManager


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response"""
    return ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="This is a test response"
                ),
                finish_reason="stop"
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
    )


@pytest.mark.asyncio
async def test_openai_provider_generate(mock_openai_response):
    """Test OpenAI provider text generation"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")

    # Mock the async client
    provider.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    result = await provider.generate(
        prompt="Hello, world!",
        system_prompt="You are a helpful assistant"
    )

    assert result == "This is a test response"
    assert provider.client.chat.completions.create.called


@pytest.mark.asyncio
async def test_openai_provider_generate_without_system_prompt(mock_openai_response):
    """Test generation without system prompt"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    provider.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    result = await provider.generate(prompt="Hello!")

    assert result == "This is a test response"


def test_openai_provider_count_tokens():
    """Test token counting"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")

    # Simple text should have some tokens
    text = "Hello, world!"
    tokens = provider.count_tokens(text)

    assert isinstance(tokens, int)
    assert tokens > 0


@pytest.mark.asyncio
async def test_openai_provider_empty_response():
    """Test handling of empty response"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")

    # Create response with None content
    empty_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=None
                ),
                finish_reason="stop"
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10
        )
    )

    provider.client.chat.completions.create = AsyncMock(return_value=empty_response)

    result = await provider.generate(prompt="Hello!")

    assert result == ""


@pytest.mark.asyncio
async def test_llm_manager_initialization():
    """Test LLM manager initialization"""
    with patch("app.core.llm.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.llm_model = "gpt-4"

        manager = LLMManager()

        assert manager.is_available()
        assert manager.provider is not None


@pytest.mark.asyncio
async def test_llm_manager_no_api_key():
    """Test LLM manager without API key"""
    with patch("app.core.llm.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = ""
        mock_settings.llm_model = "gpt-4"

        manager = LLMManager()

        assert not manager.is_available()
        assert manager.provider is None


@pytest.mark.asyncio
async def test_llm_manager_generate_no_provider():
    """Test generate without configured provider"""
    with patch("app.core.llm.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = ""

        manager = LLMManager()

        with pytest.raises(RuntimeError, match="No LLM provider configured"):
            await manager.generate(prompt="Hello!")


@pytest.mark.asyncio
async def test_llm_manager_count_tokens_no_provider():
    """Test count_tokens without configured provider"""
    with patch("app.core.llm.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = ""

        manager = LLMManager()

        with pytest.raises(RuntimeError, match="No LLM provider configured"):
            manager.count_tokens("Hello!")
