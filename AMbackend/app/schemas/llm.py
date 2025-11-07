"""LLM schemas for requests and responses"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message"""

    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class LLMResponse(BaseModel):
    """LLM API response"""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider name")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage stats")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class LLMRequest(BaseModel):
    """LLM API request"""

    messages: List[Message] = Field(..., description="Chat messages")
    model: str = Field(..., description="Model to use")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(0.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(0.0, description="Presence penalty")
