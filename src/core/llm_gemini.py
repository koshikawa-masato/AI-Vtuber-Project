"""
Google Gemini LLM Provider

Cloud LLM provider using Google Gemini API.

Features:
- High-quality responses
- Multimodal capabilities (text, images, video)
- Models: gemini-1.5-pro, gemini-1.5-flash

Pricing (as of 2025-11-04):
- gemini-1.5-pro: $1.25/1M input, $5.00/1M output
- gemini-1.5-flash: $0.075/1M input, $0.30/1M output

Installation:
    pip install google-generativeai

Author: koshikawa-masato
Date: 2025-11-04
"""

import os
import time
from typing import Optional

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "Google Generative AI package not installed. "
        "Please install it with: pip install google-generativeai"
    )

from .llm_provider import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""

    # Pricing (USD per 1M tokens)
    PRICING = {
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash"
    ):
        """
        Initialize Gemini provider

        Args:
            api_key: Google API key (reads from GOOGLE_API_KEY env if None)
            model: Model name (gemini-1.5-pro / gemini-1.5-flash)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key not provided. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(model)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        Generate response using Gemini API

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content and cost
        """
        start_time = time.time()

        # Gemini uses system instruction in the prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Call Gemini API
        try:
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")

        latency = time.time() - start_time

        # Gemini doesn't provide exact token count in response
        # Rough estimate: 1 token ≈ 4 characters (for English/Japanese mix)
        input_tokens = len(full_prompt) // 4
        output_tokens = len(response.text) // 4
        total_tokens = input_tokens + output_tokens

        cost = self.estimate_cost(input_tokens, output_tokens)

        return LLMResponse(
            content=response.text,
            model=self.model,
            provider="gemini",
            tokens_used=total_tokens,
            cost_estimate=cost,
            latency=latency
        )

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "gemini"

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
        pricing = self.PRICING.get(self.model, self.PRICING["gemini-1.5-flash"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
