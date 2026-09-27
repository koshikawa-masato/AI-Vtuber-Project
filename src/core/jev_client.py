"""Jev through cloud providers, or Lev through a loopback-only endpoint."""

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit
from dataclasses import dataclass
from time import perf_counter

import httpx


class JevError(RuntimeError):
    """Safe error code suitable for reports (never includes request/response text)."""


@dataclass(frozen=True)
class JevEvaluation:
    probabilities: dict[str, float]
    model: str
    usage: dict
    elapsed_ms: float
    provider: str = "typesafe"
    reported_cost_usd: float | None = None


class JevClient:
    ENDPOINT = "https://api.typesafe.ai/v1/systemone"
    BRIDGE = Path(__file__).resolve().parents[2] / "tools" / "jev_gateway" / "bridge.mjs"

    def __init__(self, *, provider=None, api_key=None, model=None, timeout=None, transport=None):
        self.provider = provider or os.getenv("JEV_PROVIDER") or "vercel"
        if self.provider not in ("vercel", "typesafe", "lev"):
            raise ValueError("JEV_PROVIDER must be vercel, typesafe, or lev")
        self.key_env = "AI_GATEWAY_API_KEY" if self.provider == "vercel" else "TYPESAFE_API_KEY"
        self.api_key = api_key if api_key is not None else os.getenv(self.key_env, "")
        self.endpoint = self.ENDPOINT
        if self.provider == "lev":
            self.endpoint = os.getenv("LEV_ENDPOINT", "http://127.0.0.1:18009/v1/systemone")
            address = urlsplit(self.endpoint)
            if (address.scheme != "http" or address.hostname not in ("127.0.0.1", "::1")
                    or address.username or address.password or address.query or address.fragment
                    or address.path != "/v1/systemone"):
                raise ValueError("LEV_ENDPOINT must be a loopback HTTP System One endpoint")
            self.api_key = "local"
        default_model = "typesafe-ai/jev" if self.provider == "vercel" else "jev-1.13.0"
        self.model = model or os.getenv("JEV_MODEL") or default_model
        if self.provider == "lev":
            self.model = model or os.getenv("LEV_MODEL", "lev-latest")
        if self.provider == "vercel" and not self.model.startswith("typesafe-ai/"):
            raise ValueError("Vercel requires a typesafe-ai/ model ID")
        self.timeout = float(timeout if timeout is not None else os.getenv("JEV_TIMEOUT_SECONDS", "5"))
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("JEV_TIMEOUT_SECONDS must be positive and finite")
        self.transport = transport

    def _evaluate_gateway(self, state, questions):
        node = os.getenv("JEV_NODE_BIN") or shutil.which("node")
        if not node:
            raise JevError("node_not_found")
        if not (self.BRIDGE.parent / "node_modules" / "ai" / "package.json").is_file():
            raise JevError("gateway_sdk_not_installed")
        try:
            completed = subprocess.run(
                [node, str(self.BRIDGE)],
                input=json.dumps({"model": self.model, "state": state, "questions": questions,
                                  "timeoutMs": max(1, int(self.timeout * 1000))}),
                text=True, capture_output=True, timeout=self.timeout + 5,
                env={**os.environ, "AI_GATEWAY_API_KEY": self.api_key},
            )
        except subprocess.TimeoutExpired:
            raise JevError("timeout") from None
        except OSError:
            raise JevError("gateway_bridge_unavailable") from None
        try:
            payload = json.loads(completed.stdout)
        except ValueError:
            raise JevError("gateway_bridge_failed") from None
        if not isinstance(payload, dict):
            raise JevError("invalid_response")
        if completed.returncode or "error" in payload:
            code = payload.get("error")
            if not isinstance(code, str) or not re.fullmatch(r"http_[1-5][0-9]{2}|timeout|gateway_evaluation_failed|free_tier_rate_limit", code):
                code = "gateway_bridge_failed"
            raise JevError(code)
        return payload

    def evaluate_noul(self, state: dict, questions: dict) -> JevEvaluation:
        if not self.api_key.strip() or self.api_key.startswith(("your_", "replace_", "<")):
            raise JevError("missing_api_key")
        started = perf_counter()
        if self.provider == "vercel":
            payload = self._evaluate_gateway(state, questions)
        else:
            payload = self._evaluate_direct(state, questions)
        return self._parse_result(payload, questions, started)

    def _evaluate_direct(self, state, questions):
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport, follow_redirects=False,
                              trust_env=self.provider != "lev") as client:
                response = client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "state": state, "questions": questions},
                )
            if response.status_code != 200:
                raise JevError(f"http_{response.status_code}")
            payload = response.json()
        except httpx.TimeoutException:
            raise JevError("timeout") from None
        except httpx.HTTPError:
            raise JevError("transport_error") from None
        except ValueError:
            raise JevError("invalid_json") from None
        return payload

    def _parse_result(self, payload, questions, started):
        if not isinstance(payload, dict) or not isinstance(payload.get("model"), str) or not payload["model"].strip():
            raise JevError("invalid_response")
        answers = payload.get("answers")
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise JevError("invalid_answers")
        probabilities = {}
        answer_type, probability_key = ("boolean", "probability") if self.provider == "vercel" else ("noul", "noul")
        for key, answer in answers.items():
            if not isinstance(answer, dict) or answer.get("type") != answer_type:
                raise JevError("invalid_answer_type")
            value = answer.get(probability_key)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise JevError("invalid_probability")
            probabilities[key] = float(value)
        # Missing usage is unknown, never fabricated from string length or set to zero.
        raw_usage = payload.get("usage")
        usage = {}
        if isinstance(raw_usage, dict):
            names = {"inputTokens": "input_tokens", "outputTokens": "output_tokens"} if self.provider == "vercel" else {
                "input_tokens": "input_tokens", "output_tokens": "output_tokens"}
            usage = {names[key]: value for key, value in raw_usage.items()
                     if key in names and type(value) is int and value >= 0}
        reported_cost = None
        if self.provider == "vercel":
            raw_cost = payload.get("gatewayCost")
            if type(raw_cost) in (str, int, float):
                try:
                    value = float(raw_cost)
                    if math.isfinite(value) and value >= 0:
                        reported_cost = value
                except ValueError:
                    pass
        return JevEvaluation(probabilities, payload["model"], usage, (perf_counter() - started) * 1000,
                             self.provider, reported_cost)
