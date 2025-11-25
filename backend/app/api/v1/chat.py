"""Chat endpoint for LLM interactions"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.llm import llm_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    system_prompt: Optional[str] = Field(None, max_length=2000, description="Optional system prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum tokens to generate")


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str = Field(..., description="LLM generated answer")
    tokens_used: Optional[int] = Field(None, description="Number of tokens in the answer")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Simple chat endpoint using LLM

    Args:
        request: Chat request with message and optional parameters

    Returns:
        ChatResponse with generated answer

    Raises:
        HTTPException: If LLM is not available or generation fails
    """
    if not llm_manager.is_available():
        logger.error("LLM provider not available")
        raise HTTPException(
            status_code=503,
            detail="LLM service is not available. Please check API key configuration."
        )

    try:
        # Generate response
        answer = await llm_manager.generate(
            prompt=request.message,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Count tokens in response
        tokens_used = llm_manager.count_tokens(answer)

        logger.info(f"Chat request processed: {len(request.message)} chars -> {tokens_used} tokens")

        return ChatResponse(
            answer=answer,
            tokens_used=tokens_used
        )

    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )
