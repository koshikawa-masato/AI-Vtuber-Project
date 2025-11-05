"""
Ollama LLM Provider

Local LLM provider using Ollama runtime.

Features:
- No API cost (runs locally)
- Full privacy (data never leaves the machine)
- Models: qwen2.5:3b, qwen2.5:7b, qwen2.5:14b, qwen2.5:32b

Author: koshikawa-masato
Date: 2025-11-04
"""

import requests
import time
from typing import Optional
from .llm_provider import BaseLLMProvider, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:32b"
    ):
        """
        Initialize Ollama provider

        Args:
            base_url: Ollama server URL
            model: Model name (qwen2.5:3b/7b/14b/32b)
        """
        self.base_url = base_url
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        Generate response using Ollama

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content
        """
        start_time = time.time()

        # Build request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Call Ollama API
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300  # 5 minutes timeout
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")

        latency = time.time() - start_time
        data = response.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=self.model,
            provider="ollama",
            tokens_used=None,  # Ollama doesn't provide token count in response
            cost_estimate=0.0,  # Local LLM is free
            latency=latency
        )

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "ollama"

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
            0.0 (local LLM is free)
        """
        return 0.0  # Local LLM has no API cost
