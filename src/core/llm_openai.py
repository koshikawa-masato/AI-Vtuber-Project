"""
OpenAI LLM Provider

Cloud LLM provider using OpenAI API.

Features:
- High-quality responses
- Fast inference
- Models: gpt-4o, gpt-4o-mini

Pricing (as of 2025-11-04):
- gpt-4o: $2.50/1M input, $10.00/1M output
- gpt-4o-mini: $0.150/1M input, $0.600/1M output

Installation:
    pip install openai

Author: koshikawa-masato
Date: 2025-11-04
"""

import os
import time
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    raise ImportError(
        "OpenAI package not installed. "
        "Please install it with: pip install openai"
    )

from .llm_provider import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""

    # Pricing (USD per 1M tokens)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize OpenAI provider

        Args:
            api_key: OpenAI API key (reads from OPENAI_API_KEY env if None)
            model: Model name (gpt-4o / gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        Generate response using OpenAI API

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content and cost
        """
        start_time = time.time()

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

        latency = time.time() - start_time

        # Extract usage and cost
        usage = response.usage
        cost = self.estimate_cost(usage.prompt_tokens, usage.completion_tokens)

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="openai",
            tokens_used=usage.total_tokens,
            cost_estimate=cost,
            latency=latency
        )

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "openai"

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o-mini"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
