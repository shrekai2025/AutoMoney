"""LLM Provider abstract base class"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.schemas.llm import LLMResponse, Message


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str, base_url: str):
        """
        Initialize LLM provider

        Args:
            api_key: API key for authentication
            base_url: Base URL for API endpoint
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Send chat completion request

        Args:
            messages: List of chat messages
            model: Model name/identifier
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object with generated content

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider

        Returns:
            List of model names
        """
        pass

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Format messages to provider-specific format

        Args:
            messages: List of Message objects

        Returns:
            List of message dictionaries
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def estimate_cost(
        self, messages: List[Message], model: str, completion_tokens: int = 100
    ) -> float:
        """
        Estimate cost for a completion request

        Args:
            messages: Input messages
            model: Model name
            completion_tokens: Expected completion tokens

        Returns:
            Estimated cost in USD
        """
        # Default implementation - should be overridden by providers
        return 0.0
