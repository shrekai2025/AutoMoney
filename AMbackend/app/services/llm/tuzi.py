"""Tuzi (兔子) LLM Provider implementation"""

from typing import List, Optional
import httpx

from app.services.llm.base import LLMProvider
from app.schemas.llm import LLMResponse, Message


class TuziProvider(LLMProvider):
    """Tuzi API provider - Supports both Claude Messages API and OpenAI Chat Completions API"""

    # Model pricing (per 1M tokens) - approximate values for Tuzi
    MODEL_PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 2.5, "output": 12.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-opus-4-1-thinking": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-5-thinking-all": {"input": 3.0, "output": 15.0},
        "gpt-4o": {"input": 4.5, "output": 13.5},
        "gpt-4o-mini": {"input": 0.12, "output": 0.5},
        "chatgpt-4o-latest": {"input": 4.5, "output": 13.5},  # GPT-5
    }

    # Models that use OpenAI Chat Completions API format
    OPENAI_FORMAT_MODELS = {
        "chatgpt-4o-latest",  # GPT-5
        "gpt-4o",
        "gpt-4o-mini",
    }

    def __init__(self, api_key: str, base_url: str = "https://api.tu-zi.com"):
        """
        Initialize Tuzi provider

        Args:
            api_key: Tuzi API key
            base_url: Tuzi API base URL (default: https://api.tu-zi.com)
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
        Send chat completion request to Tuzi
        Automatically chooses between Claude Messages API and OpenAI Chat Completions API

        Args:
            messages: List of chat messages
            model: Model identifier (e.g., "claude-sonnet-4-5-thinking-all" or "chatgpt-4o-latest")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Determine which API format to use based on model
        use_openai_format = model in self.OPENAI_FORMAT_MODELS

        if use_openai_format:
            return await self._chat_openai_format(messages, model, temperature, max_tokens, **kwargs)
        else:
            return await self._chat_claude_format(messages, model, temperature, max_tokens, **kwargs)

    async def _chat_claude_format(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs,
    ) -> LLMResponse:
        """Handle Claude Messages API format"""
        url = f"{self.base_url}/v1/messages"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Convert our Message format to Claude Messages API format
        formatted_messages = self._format_messages(messages)

        payload = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": max_tokens or 4096,  # Claude requires max_tokens
        }

        # Add optional parameters
        if temperature is not None:
            payload["temperature"] = temperature

        # Add any extra kwargs
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract content and usage (Claude Messages API format)
        # Claude returns content as an array of content blocks
        content_blocks = data.get("content", [])
        content = ""
        if content_blocks:
            # Join all text blocks
            content = "".join(
                block.get("text", "")
                for block in content_blocks
                if block.get("type") == "text"
            )

        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model,
            provider="tuzi",
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
            metadata={
                "finish_reason": data.get("stop_reason"),
                "id": data.get("id"),
                "model": data.get("model"),
                "role": data.get("role"),
            },
        )

    async def _chat_openai_format(
        self,
        messages: List[Message],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs,
    ) -> LLMResponse:
        """Handle OpenAI Chat Completions API format (for GPT-5)"""
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Convert our Message format to OpenAI format
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": False,
        }

        # Add max_tokens if specified
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add response_format for JSON mode if specified in kwargs
        if "response_format" in kwargs:
            payload["response_format"] = kwargs.pop("response_format")

        # Add any extra kwargs
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract content from OpenAI format response
        choices = data.get("choices", [])
        content = ""
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model,
            provider="tuzi",
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            metadata={
                "finish_reason": choices[0].get("finish_reason") if choices else None,
                "id": data.get("id"),
                "model": data.get("model"),
            },
        )

    def get_available_models(self) -> List[str]:
        """Get list of available Tuzi models"""
        return list(self.MODEL_PRICING.keys())

    async def estimate_cost(
        self, messages: List[Message], model: str, completion_tokens: int = 100
    ) -> float:
        """
        Estimate cost for Tuzi completion

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
