"""
LLM Tracing Module with LangSmith Integration

This module provides LLM call tracing capabilities using LangSmith.
It wraps Ollama/OpenAI/Gemini API calls to track:
- Cost per request
- Latency
- Token usage
- Input/Output
- Error rates

Usage:
    from src.core.llm_tracing import TracedLLM

    llm = TracedLLM(provider="ollama", model="qwen2.5:14b")
    response = llm.generate("Tell me about AI VTubers")
"""

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx
from langsmith import traceable
from langsmith.run_trees import RunTree


class TracedLLM:
    """
    LLM wrapper with LangSmith tracing

    Supports:
    - Ollama (local)
    - OpenAI API
    - Google Gemini API
    """

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "qwen2.5:14b",
        ollama_url: str = "http://localhost:11434",
        project_name: str = "botan-project"
    ):
        """
        Initialize TracedLLM

        Args:
            provider: "ollama", "openai", or "gemini"
            model: Model name
            ollama_url: Ollama server URL (for provider="ollama")
            project_name: LangSmith project name
        """
        self.provider = provider
        self.model = model
        self.ollama_url = ollama_url
        self.project_name = project_name

        # Check if LangSmith is enabled
        self.langsmith_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

        if self.langsmith_enabled:
            self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
            if not self.langsmith_api_key:
                print("[WARNING] LANGSMITH_TRACING=true but LANGSMITH_API_KEY not set")
                self.langsmith_enabled = False

    @traceable(
        run_type="llm",
        name="ollama_generate",
        project_name=None  # Will be set dynamically
    )
    def _ollama_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Call Ollama API with tracing

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Response dict with 'response', 'tokens', 'latency_ms'
        """
        start_time = time.time()

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

            latency_ms = (time.time() - start_time) * 1000

            return {
                "response": result.get("response", ""),
                "tokens": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                "latency_ms": latency_ms,
                "model": self.model,
                "provider": self.provider
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "response": "",
                "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": latency_ms,
                "model": self.model,
                "provider": self.provider,
                "error": str(e)
            }

    @traceable(
        run_type="llm",
        name="openai_generate",
        project_name=None
    )
    def _openai_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Call OpenAI API with tracing"""
        try:
            import openai

            start_time = time.time()

            client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            latency_ms = (time.time() - start_time) * 1000

            return {
                "response": response.choices[0].message.content,
                "tokens": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "latency_ms": latency_ms,
                "model": self.model,
                "provider": self.provider
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "response": "",
                "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": latency_ms,
                "model": self.model,
                "provider": self.provider,
                "error": str(e)
            }

    @traceable(
        run_type="llm",
        name="gemini_generate",
        project_name=None
    )
    def _gemini_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Call Google Gemini API with tracing"""
        try:
            import google.generativeai as genai

            start_time = time.time()

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel(self.model)

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )

            latency_ms = (time.time() - start_time) * 1000

            return {
                "response": response.text,
                "tokens": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                },
                "latency_ms": latency_ms,
                "model": self.model,
                "provider": self.provider
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "response": "",
                "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": latency_ms,
                "model": self.model,
                "provider": self.provider,
                "error": str(e)
            }

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate text with LLM (with automatic tracing)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            metadata: Additional metadata for tracing (e.g., character, topic)

        Returns:
            Response dict with 'response', 'tokens', 'latency_ms'
        """
        # Route to appropriate provider
        if self.provider == "ollama":
            result = self._ollama_generate(prompt, temperature, max_tokens)
        elif self.provider == "openai":
            result = self._openai_generate(prompt, temperature, max_tokens)
        elif self.provider == "gemini":
            result = self._gemini_generate(prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        # Add metadata
        if metadata:
            result["metadata"] = metadata

        # Add timestamp
        result["timestamp"] = datetime.now().isoformat()

        return result


class ThreeSistersTracedCouncil:
    """
    Three Sisters Council with LangSmith Tracing

    This is a wrapper around ThreeSistersCouncil that adds tracing.
    """

    def __init__(
        self,
        db_path: str = "sisters_memory.db",
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
        project_name: str = "three-sisters-council"
    ):
        """
        Initialize council with tracing

        Args:
            db_path: Path to sisters_memory.db
            ollama_url: Ollama server URL
            model: Model name
            project_name: LangSmith project name
        """
        self.db_path = db_path
        self.llm = TracedLLM(
            provider="ollama",
            model=model,
            ollama_url=ollama_url,
            project_name=project_name
        )

    @traceable(
        run_type="chain",
        name="three_sisters_consultation",
        project_name=None
    )
    def consult(
        self,
        proposal: Dict[str, Any],
        characters: List[str] = ["botan", "kasho", "yuri"]
    ) -> Dict[str, Any]:
        """
        Consult all three sisters on a proposal

        Args:
            proposal: Proposal dict with 'title', 'background', 'implementation', 'expected_effects'
            characters: List of characters to consult (default: all three)

        Returns:
            Dict with each character's opinion
        """
        opinions = {}

        for character in characters:
            # Build prompt (character-specific logic would go here)
            prompt = self._build_consultation_prompt(character, proposal)

            # Generate with tracing
            result = self.llm.generate(
                prompt,
                temperature=0.8,
                max_tokens=2048,
                metadata={
                    "character": character,
                    "proposal_title": proposal.get("title", ""),
                    "consultation_type": "proposal_review"
                }
            )

            opinions[character] = {
                "response": result["response"],
                "latency_ms": result["latency_ms"],
                "tokens": result["tokens"]
            }

        return opinions

    def _build_consultation_prompt(
        self,
        character: str,
        proposal: Dict[str, Any]
    ) -> str:
        """Build consultation prompt for a character"""
        # Simplified version - full implementation would use actual character prompts
        return f"Character: {character}\nProposal: {proposal.get('title', '')}\n\nPlease provide your opinion."


if __name__ == "__main__":
    # Example usage
    print("Testing TracedLLM...")

    llm = TracedLLM(provider="ollama", model="qwen2.5:3b")

    result = llm.generate(
        prompt="Tell me about AI VTubers in one sentence.",
        temperature=0.7,
        max_tokens=100,
        metadata={"test": "example"}
    )

    print(f"\n✅ Response: {result['response']}")
    print(f"✅ Latency: {result['latency_ms']:.2f}ms")
    print(f"✅ Tokens: {result['tokens']}")

    if os.getenv("LANGSMITH_TRACING") == "true":
        print("\n🔍 Check LangSmith dashboard: https://smith.langchain.com")
