"""
LLM Provider Abstraction Layer

This module provides a unified interface for different LLM providers:
- Ollama (local LLM)
- OpenAI API
- Google Gemini API

Design Philosophy:
    "LLM is just a 'voice' for Botan. The essence of Botan lies in the logic layer."
    - personality_core.py (8-axis personality model)
    - memory_retrieval_logic.py (memory retrieval)
    - speech_style_controller.py (speech style control)

Author: koshikawa-masato
Date: 2025-11-04
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time


@dataclass
class LLMResponse:
    """Standard format for LLM response across all providers"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    latency: Optional[float] = None

    def __str__(self) -> str:
        """Human-readable representation"""
        cost_str = f"${self.cost_estimate:.6f}" if self.cost_estimate else "Free"
        tokens_str = f"{self.tokens_used} tokens" if self.tokens_used else "N/A"
        return (
            f"LLMResponse(\n"
            f"  provider={self.provider}, model={self.model}\n"
            f"  latency={self.latency:.3f}s, cost={cost_str}, tokens={tokens_str}\n"
            f"  content_length={len(self.content)} chars\n"
            f")"
        )


class BaseLLMProvider(ABC):
    """
    Base class for all LLM providers

    All providers must implement:
    - generate(): Generate response from LLM
    - get_provider_name(): Return provider name (ollama/openai/gemini)
    - get_model_name(): Return model name
    - estimate_cost(): Estimate cost in USD
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        Generate response from LLM

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse object with content, metadata, and cost
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name (ollama/openai/gemini)"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pass


class LLMProviderFactory:
    """Factory to create LLM provider instances"""

    @staticmethod
    def create(provider_type: str, **kwargs) -> BaseLLMProvider:
        """
        Create provider instance

        Args:
            provider_type: Provider type (ollama/openai/gemini)
            **kwargs: Provider-specific arguments

        Returns:
            BaseLLMProvider instance

        Raises:
            ValueError: If provider_type is unknown
        """
        provider_type = provider_type.lower()

        if provider_type == "ollama":
            from .llm_ollama import OllamaProvider
            return OllamaProvider(**kwargs)
        elif provider_type == "openai":
            from .llm_openai import OpenAIProvider
            return OpenAIProvider(**kwargs)
        elif provider_type == "gemini":
            from .llm_gemini import GeminiProvider
            return GeminiProvider(**kwargs)
        else:
            raise ValueError(
                f"Unknown provider: {provider_type}. "
                f"Supported: ollama, openai, gemini"
            )

    @staticmethod
    def create_from_env() -> BaseLLMProvider:
        """
        Create provider instance from environment variable

        Reads LLM_PROVIDER from environment (default: ollama)

        Returns:
            BaseLLMProvider instance
        """
        import os
        provider_type = os.getenv("LLM_PROVIDER", "ollama")
        return LLMProviderFactory.create(provider_type)
