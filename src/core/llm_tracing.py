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
from functools import wraps


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

    def _ollama_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Ollama API with tracing

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            image_url: Image URL or data URI (base64). Supported by VLM models (llava, gemma3, etc.)

        Returns:
            Response dict with 'response', 'tokens', 'latency_ms'
        """
        start_time = time.time()

        try:
            # Build request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            # Add image if provided (for VLM models like llava, gemma3)
            if image_url:
                # Extract base64 data from data URI (data:image/jpeg;base64,...)
                if image_url.startswith("data:"):
                    # Remove data URI prefix to get base64 string
                    base64_data = image_url.split(",", 1)[1] if "," in image_url else image_url
                    payload["images"] = [base64_data]
                else:
                    # If it's a URL, pass as-is (Ollama will fetch it)
                    payload["images"] = [image_url]

            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
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

    def _openai_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call OpenAI API with tracing (supports Vision)"""
        try:
            import openai

            start_time = time.time()

            client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

            # Build message content (text + optional image)
            if image_url:
                content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            else:
                content = prompt

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
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

    def _gemini_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call Google Gemini API with tracing (supports Vision)"""
        start_time = time.time()

        try:
            import google.generativeai as genai
            from PIL import Image
            import requests
            from io import BytesIO

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

            # Configure safety settings to be more permissive
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]

            model = genai.GenerativeModel(
                self.model,
                safety_settings=safety_settings
            )

            # Prepare content (text + optional image)
            if image_url:
                # Download or load image
                if image_url.startswith('http'):
                    # Gemini can accept image URLs directly
                    import PIL.Image
                    response_img = requests.get(image_url, stream=True)
                    response_img.raise_for_status()
                    img = PIL.Image.open(response_img.raw)
                else:
                    # Local file path
                    import PIL.Image
                    img = PIL.Image.open(image_url)

                content = [prompt, img]
            else:
                content = prompt

            response = model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )

            latency_ms = (time.time() - start_time) * 1000

            # Check if response was blocked
            if not response.candidates:
                error_msg = "Response blocked: No candidates returned"
                return {
                    "response": "",
                    "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "latency_ms": latency_ms,
                    "model": self.model,
                    "provider": self.provider,
                    "error": error_msg
                }

            candidate = response.candidates[0]

            # Check finish_reason
            finish_reason = candidate.finish_reason
            finish_reason_names = {
                0: "FINISH_REASON_UNSPECIFIED",
                1: "STOP",
                2: "MAX_TOKENS",
                3: "SAFETY",
                4: "RECITATION",
                5: "OTHER"
            }
            reason_name = finish_reason_names.get(finish_reason, f"UNKNOWN({finish_reason})")

            # Extract text safely
            try:
                response_text = response.text
            except ValueError:
                # If response.text fails, try to extract from parts
                if candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
                else:
                    response_text = ""

            # If finish_reason is not STOP and response is empty, treat as error
            if finish_reason != 1 and not response_text:  # 1 = STOP (normal completion)
                if finish_reason == 3:  # SAFETY
                    safety_info = []
                    if hasattr(candidate, 'safety_ratings'):
                        for rating in candidate.safety_ratings:
                            if rating.probability != 1:  # Not NEGLIGIBLE
                                safety_info.append(f"{rating.category.name}: {rating.probability}")

                    error_msg = f"Blocked by safety filter: {reason_name}"
                    if safety_info:
                        error_msg += f" ({', '.join(safety_info)})"
                else:
                    error_msg = f"Generation failed: {reason_name} (no content returned)"

                return {
                    "response": "",
                    "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "latency_ms": latency_ms,
                    "model": self.model,
                    "provider": self.provider,
                    "error": error_msg
                }

            # Get token counts safely
            try:
                tokens = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            except AttributeError:
                tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            return {
                "response": response_text,
                "tokens": tokens,
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
        metadata: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate text with LLM (with automatic tracing)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            metadata: Additional metadata for tracing (e.g., character, topic)
            image_url: Optional image URL or file path (for Vision models)

        Returns:
            Response dict with 'response', 'tokens', 'latency_ms'
        """
        # Get trace name from metadata or use model name
        trace_name = metadata.get("model_name", self.model) if metadata else self.model

        # Define the generation function (with prompt as argument for LangSmith Input)
        def do_generate(input_prompt: str) -> str:
            """Generate response and return just the text for clean LangSmith display"""
            if self.provider == "ollama":
                full_result = self._ollama_generate(input_prompt, temperature, max_tokens, image_url)
            elif self.provider == "openai":
                full_result = self._openai_generate(input_prompt, temperature, max_tokens, image_url)
            elif self.provider == "gemini":
                full_result = self._gemini_generate(input_prompt, temperature, max_tokens, image_url)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

            # Store full result for later use (closure)
            do_generate.full_result = full_result

            # If there's an error, raise exception for LangSmith to capture
            if "error" in full_result:
                raise RuntimeError(full_result["error"])

            # Return only response text for LangSmith Output display
            return full_result.get("response", "")

        # Apply tracing if enabled
        if self.langsmith_enabled:
            traced_func = traceable(
                run_type="llm",
                name=trace_name,
                project_name=self.project_name
            )(do_generate)
            try:
                response_text = traced_func(prompt)
                # Retrieve full result from closure
                result = do_generate.full_result
            except RuntimeError:
                # Exception was raised for LangSmith tracing, retrieve error result
                result = do_generate.full_result
        else:
            try:
                response_text = do_generate(prompt)
                result = do_generate.full_result
            except RuntimeError:
                # Retrieve error result
                result = do_generate.full_result

        # Add metadata
        if metadata:
            result["metadata"] = metadata

        # Add timestamp
        result["timestamp"] = datetime.now().isoformat()

        return result

    def sensitive_check(
        self,
        text: str,
        context: Optional[str] = None,
        speaker: Optional[str] = None,
        judge_provider: str = "openai",
        judge_model: str = "gpt-4o-mini",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform sensitive content detection using LLM as a Judge (Phase 5)

        Args:
            text: Text to check for sensitive content
            context: Optional context information (e.g., "Gaming stream", "LINE Bot user message")
            speaker: Optional speaker name (e.g., "botan", "kasho", "yuri", None for viewer)
            judge_provider: LLM provider for judgment ("openai", "gemini", "ollama")
            judge_model: LLM model for judgment (default: "gpt-4o-mini")
            metadata: Additional metadata for tracing

        Returns:
            Dict containing:
            - evaluation: Parsed evaluation result (sensitivity_level, risk_score, tier, reasoning, recommendation, sensitive_topics, suggested_response)
            - judge_response: Raw LLM response
            - judge_latency_ms: Latency in milliseconds
            - judge_tokens: Token usage
            - metadata: Original metadata + check info
        """
        start_time = time.time()

        # Build sensitive check prompt
        prompt = self._build_sensitive_check_prompt(text, context, speaker)

        # Create judge LLM instance
        judge_llm = TracedLLM(
            provider=judge_provider,
            model=judge_model,
            project_name=f"{self.project_name}-sensitive-check"
        )

        # Call judge LLM
        judge_result = judge_llm.generate(
            prompt=prompt,
            temperature=0.3,  # Low temperature for consistent judgment
            max_tokens=1024,
            metadata={
                "check_type": "sensitive_content",
                "text_length": len(text),
                "has_context": context is not None,
                "has_speaker": speaker is not None,
                **(metadata or {})
            }
        )

        judge_latency_ms = (time.time() - start_time) * 1000

        # Parse evaluation from LLM response
        evaluation = self._parse_sensitive_evaluation(judge_result.get("response", ""))

        return {
            "evaluation": evaluation,
            "judge_response": judge_result.get("response", ""),
            "judge_latency_ms": judge_latency_ms,
            "judge_tokens": judge_result.get("tokens", {}),
            "metadata": {
                "text": text[:100],  # First 100 chars
                "context": context,
                "speaker": speaker,
                "judge_provider": judge_provider,
                "judge_model": judge_model,
                **(metadata or {})
            }
        }

    def _build_sensitive_check_prompt(
        self,
        text: str,
        context: Optional[str],
        speaker: Optional[str]
    ) -> str:
        """
        Build prompt for sensitive content detection

        Args:
            text: Text to check
            context: Optional context
            speaker: Optional speaker name

        Returns:
            Prompt string
        """
        prompt = f"""You are a sensitive content detection system for VTuber livestreaming.

Your task is to analyze the following text and determine if it contains sensitive or inappropriate content.

**Text to analyze:**
"{text}"
"""

        if context:
            prompt += f"""
**Context:**
{context}
"""

        if speaker:
            prompt += f"""
**Speaker:**
{speaker} (VTuber character)
"""
        else:
            prompt += """
**Speaker:**
Viewer comment
"""

        prompt += """

**Sensitivity Tiers:**

- **Tier 1 (Critical)**: Requires immediate blocking
  - Violence, threats, self-harm, suicide
  - Sexual harassment, explicit sexual content
  - Hate speech, discrimination
  - Illegal activities

- **Tier 2 (Warning)**: Requires review and context-dependent handling
  - AI identity questions (e.g., "Are you an AI?")
  - Political or religious topics
  - Controversial social issues

- **Tier 3 (Warning)**: Gray zone, handle with care
  - Personal questions (age, romance, real identity)
  - Privacy-related questions
  - Mild insults or provocations

**Your task:**
Analyze the text and provide a JSON response with the following format:

```json
{
  "sensitivity_level": "safe|warning|critical",
  "risk_score": 0.0-1.0,
  "tier": "Tier 1|Tier 2|Tier 3|null",
  "reasoning": "Brief explanation of your judgment",
  "recommendation": "allow|review_required|block_immediate",
  "sensitive_topics": ["topic1", "topic2"],
  "suggested_response": "Safe alternative response if applicable"
}
```

**Important:**
- Be context-aware: Consider the speaker and context when making judgments
- Be strict for Tier 1 (Critical) content
- Be nuanced for Tier 2-3 (Warning) content
- Return ONLY the JSON object, no additional text

Analyze the text now:"""

        return prompt

    def _parse_sensitive_evaluation(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response for sensitive evaluation

        Args:
            response: LLM response string

        Returns:
            Parsed evaluation dict
        """
        import json
        import re

        # Extract JSON from response (in case LLM adds extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)

        if not json_match:
            # Parsing failed, return error result
            return {
                "sensitivity_level": "error",
                "risk_score": 0.0,
                "tier": None,
                "reasoning": "Failed to parse LLM response",
                "recommendation": "error",
                "sensitive_topics": [],
                "suggested_response": "",
                "parse_error": True
            }

        try:
            evaluation = json.loads(json_match.group(0))

            # Validate required fields
            required_fields = ["sensitivity_level", "risk_score", "reasoning", "recommendation"]
            for field in required_fields:
                if field not in evaluation:
                    evaluation[field] = "unknown" if field != "risk_score" else 0.0

            # Ensure sensitive_topics is a list
            if "sensitive_topics" not in evaluation:
                evaluation["sensitive_topics"] = []

            # Ensure suggested_response exists
            if "suggested_response" not in evaluation:
                evaluation["suggested_response"] = ""

            return evaluation

        except json.JSONDecodeError as e:
            return {
                "sensitivity_level": "error",
                "risk_score": 0.0,
                "tier": None,
                "reasoning": f"JSON parse error: {str(e)}",
                "recommendation": "error",
                "sensitive_topics": [],
                "suggested_response": "",
                "parse_error": True
            }


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
