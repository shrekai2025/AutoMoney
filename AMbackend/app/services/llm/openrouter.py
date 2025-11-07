"""OpenRouter LLM Provider implementation"""

from typing import List, Optional
import httpx

from app.services.llm.base import LLMProvider
from app.schemas.llm import LLMResponse, Message


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider"""

    # Model pricing (per 1M tokens) - approximate values
    MODEL_PRICING = {
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3.5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "anthropic/claude-sonnet-4.5": {"input": 3.0, "output": 15.0},  # Claude Sonnet 4.5
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "anthropic/claude-opus-4": {"input": 15.0, "output": 75.0},
        "openai/gpt-4o": {"input": 5.0, "output": 15.0},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "openai/chatgpt-4o-latest": {"input": 5.0, "output": 15.0},
        "google/gemini-pro-1.5": {"input": 1.25, "output": 5.0},
    }

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        """
        Initialize OpenRouter provider

        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter API base URL
        """
        super().__init__(api_key, base_url)

    async def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Send chat completion request to OpenRouter

        Args:
            messages: List of chat messages
            model: Model identifier (e.g., "openai/gpt-4o")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://automoney.ai",  # Optional
            "X-Title": "AutoMoney",  # Optional
        }

        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add response_format for JSON mode if specified
        if "response_format" in kwargs:
            payload["response_format"] = kwargs.pop("response_format")

        # Add any extra kwargs
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract content and usage
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model,
            provider="openrouter",
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            metadata={
                "finish_reason": data["choices"][0].get("finish_reason"),
                "id": data.get("id"),
            },
        )

    def get_available_models(self) -> List[str]:
        """Get list of available OpenRouter models"""
        return list(self.MODEL_PRICING.keys())

    async def estimate_cost(
        self, messages: List[Message], model: str, completion_tokens: int = 100
    ) -> float:
        """
        Estimate cost for OpenRouter completion

        Args:
            messages: Input messages
            model: Model identifier
            completion_tokens: Expected completion tokens

        Returns:
            Estimated cost in USD
        """
        if model not in self.MODEL_PRICING:
            return 0.0

        # Rough token estimation (4 chars ≈ 1 token)
        total_chars = sum(len(msg.content) for msg in messages)
        prompt_tokens = total_chars // 4

        pricing = self.MODEL_PRICING[model]
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
