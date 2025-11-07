"""LLM Manager for managing multiple providers"""

from typing import Dict, List, Optional
from enum import Enum

from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.openrouter import OpenRouterProvider
from app.services.llm.tuzi import TuziProvider
from app.schemas.llm import LLMResponse, Message


class ProviderType(str, Enum):
    """LLM provider types"""

    OPENROUTER = "openrouter"
    TUZI = "tuzi"


class AgentLLMConfig:
    """LLM configuration for different agents"""

    # Agent-specific LLM configurations
    AGENT_CONFIGS = {
        "system_layer": {
            "provider": ProviderType.OPENROUTER,
            "model": "openai/gpt-4o-mini",
            "temperature": 0.3,
        },
        # Research Chat Agents
        "super_agent": {
            "provider": ProviderType.TUZI,
            "model": "chatgpt-4o-latest",  # GPT-5 for fast routing
            "temperature": 0.3,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},  # Force JSON output
        },
        "planning_agent": {
            "provider": ProviderType.OPENROUTER,
            "model": "anthropic/claude-sonnet-4.5",  # Claude Sonnet 4.5 via OpenRouter
            "temperature": 0.5,
            "max_tokens": 200000,  # 200k tokens
            # Claude via OpenRouter doesn't support response_format, relies on prompt
        },
        "general_analysis_agent": {
            "provider": ProviderType.OPENROUTER,
            "model": "anthropic/claude-sonnet-4.5",  # Claude Sonnet 4.5 via OpenRouter
            "temperature": 0.6,
            "max_tokens": 200000,  # 200k tokens
            # Claude via OpenRouter doesn't support response_format, relies on prompt
        },
        # Business Agents (used by both Research Chat and Strategy)
        "macro_agent": {
            "provider": ProviderType.OPENROUTER,
            "model": "anthropic/claude-sonnet-4.5",  # Claude Sonnet 4.5 via OpenRouter
            "temperature": 1.0,
            "max_tokens": 200000,  # 200k tokens
            # Claude via OpenRouter doesn't support response_format, relies on prompt
        },
        "onchain_agent": {
            "provider": ProviderType.OPENROUTER,
            "model": "anthropic/claude-sonnet-4.5",  # Claude Sonnet 4.5 via OpenRouter
            "temperature": 0.7,
            "max_tokens": 200000,  # 200k tokens
            # Claude via OpenRouter doesn't support response_format, relies on prompt
        },
        "ta_agent": {
            "provider": ProviderType.OPENROUTER,
            "model": "anthropic/claude-sonnet-4.5",  # Claude Sonnet 4.5 via OpenRouter
            "temperature": 0.6,
            "max_tokens": 200000,  # 200k tokens
            # Claude via OpenRouter doesn't support response_format, relies on prompt
        },
    }


class LLMManager:
    """Manager for multiple LLM providers with dynamic switching"""

    def __init__(self):
        """Initialize LLM manager with all configured providers"""
        self.providers: Dict[ProviderType, LLMProvider] = {}

        # Initialize OpenRouter if configured
        if settings.OPENROUTER_API_KEY:
            self.providers[ProviderType.OPENROUTER] = OpenRouterProvider(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
            )

        # Initialize Tuzi if configured
        if settings.TUZI_API_KEY:
            self.providers[ProviderType.TUZI] = TuziProvider(
                api_key=settings.TUZI_API_KEY, base_url=settings.TUZI_BASE_URL
            )

    async def chat(
        self,
        messages: List[Message],
        provider: Optional[ProviderType] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Send chat completion request to specified provider

        Args:
            messages: List of chat messages
            provider: Provider to use (default from settings)
            model: Model to use (default from settings)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If provider not available
            Exception: If API call fails
        """
        # Use default provider if not specified
        if provider is None:
            provider = ProviderType(settings.DEFAULT_LLM_PROVIDER)

        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not configured")

        # Use default model if not specified
        if model is None:
            model = settings.DEFAULT_LLM_MODEL

        provider_instance = self.providers[provider]

        return await provider_instance.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def chat_for_agent(
        self,
        agent_name: str,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Send chat request using agent-specific configuration

        Args:
            agent_name: Name of the agent (e.g., "macro_agent")
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content
        """
        config = AgentLLMConfig.AGENT_CONFIGS.get(agent_name)

        if config is None:
            # Use default configuration
            return await self.chat(messages=messages, max_tokens=max_tokens, **kwargs)

        provider = config["provider"]
        model = config["model"]
        temperature = config.get("temperature", 0.7)

        # Use agent-specific max_tokens if not provided and config has it
        if max_tokens is None:
            max_tokens = config.get("max_tokens")

        # Merge config-level response_format with kwargs
        # Config takes precedence if specified
        if "response_format" in config and "response_format" not in kwargs:
            kwargs["response_format"] = config["response_format"]

        try:
            return await self.chat(
                messages=messages,
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except Exception as e:
            # Try fallback if configured
            fallback = config.get("fallback")
            if fallback:
                print(f"Primary provider failed, trying fallback: {e}")

                # Merge fallback response_format if present
                fallback_kwargs = kwargs.copy()
                if "response_format" in fallback:
                    fallback_kwargs["response_format"] = fallback["response_format"]

                return await self.chat(
                    messages=messages,
                    provider=fallback["provider"],
                    model=fallback["model"],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **fallback_kwargs,
                )
            raise

    async def estimate_cost(
        self,
        messages: List[Message],
        provider: ProviderType,
        model: str,
        completion_tokens: int = 100,
    ) -> float:
        """
        Estimate cost for a completion request

        Args:
            messages: Input messages
            provider: Provider to use
            model: Model identifier
            completion_tokens: Expected completion tokens

        Returns:
            Estimated cost in USD
        """
        if provider not in self.providers:
            return 0.0

        provider_instance = self.providers[provider]
        return await provider_instance.estimate_cost(messages, model, completion_tokens)

    def get_available_models(self, provider: ProviderType) -> List[str]:
        """
        Get list of available models for a provider

        Args:
            provider: Provider type

        Returns:
            List of model names
        """
        if provider not in self.providers:
            return []

        return self.providers[provider].get_available_models()

    def get_available_providers(self) -> List[str]:
        """
        Get list of configured providers

        Returns:
            List of provider names
        """
        return [p.value for p in self.providers.keys()]


# Global LLM manager instance
llm_manager = LLMManager()
