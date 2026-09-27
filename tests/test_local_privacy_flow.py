import json
from types import SimpleNamespace

import httpx
import pytest

from src.core.jev_client import JevClient, JevError
from src.line_bot_vps import fact_check_pipeline as facts
from src.line_bot_vps import privacy_guard as guard


class LocalJudge:
    def __init__(self, probability=0.05, error=None):
        self.probability = probability
        self.error = error
        self.calls = []

    def evaluate_noul(self, state, questions):
        self.calls.append(state)
        if self.error:
            raise self.error
        return SimpleNamespace(probabilities={"sensitive": self.probability})


@pytest.mark.parametrize("probability,blocked,review", [
    (0.05, False, False), (0.3, False, False), (0.4, True, True),
    (0.69, True, True), (0.7, True, False), (0.95, True, False),
])
def test_uncertainty_is_held(probability, blocked, review):
    result = guard.screen("病院についての話", LocalJudge(probability))
    assert (result.blocked, result.review_required) == (blocked, review)


def test_failure_is_not_an_incident():
    result = guard.screen("病院について", LocalJudge(error=JevError("timeout")))
    assert result.blocked and result.review_required and not result.kinds


def test_cloud_privacy_client_is_rejected_without_request():
    def forbidden(request):
        pytest.fail("Cloud must not receive privacy data")
    client = JevClient(provider="typesafe", api_key="test", transport=httpx.MockTransport(forbidden))
    result = guard.screen("私の年収は420万円です", client)
    assert result.blocked and result.review_required


def test_default_privacy_provider_is_local(monkeypatch):
    calls = []
    def factory(**kwargs):
        calls.append(kwargs)
        return LocalJudge()
    original = guard.JevClient
    class Factory(original):
        def __new__(cls, **kwargs):
            return factory(**kwargs)
    monkeypatch.setattr(guard, "JevClient", Factory)
    monkeypatch.setenv("JEV_PROVIDER", "typesafe")
    assert not guard.screen("病院のドラマ", force_context=True).blocked
    assert calls == [{"provider": "lev"}]


@pytest.mark.parametrize("endpoint", [
    "https://api.typesafe.ai/v1/systemone", "http://192.168.1.1/v1/systemone",
    "http://localhost/v1/systemone", "http://127.0.0.1@evil.test/v1/systemone",
    "http://127.0.0.1/v1/systemone?forward=cloud",
])
def test_lev_rejects_non_loopback_or_modified_endpoint(monkeypatch, endpoint):
    monkeypatch.setenv("LEV_ENDPOINT", endpoint)
    with pytest.raises(ValueError):
        JevClient(provider="lev")


def test_local_protocol_ignores_cloud_key_and_model(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "cloud-secret-test")
    monkeypatch.setenv("JEV_MODEL", "jev-1.13.0")
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"model": "lev", "answers": {"safe": {"type": "noul", "noul": 0.1}}})
    client = JevClient(provider="lev", transport=httpx.MockTransport(handler))
    assert client.evaluate_noul({}, {"safe": {"type": "noul"}}).provider == "lev"
    assert seen[0].headers["authorization"] == "Bearer local"
    assert json.loads(seen[0].content)["model"] == "lev-latest"


def test_nested_history_is_checked_before_local_model():
    judge = LocalJudge()
    result = guard.screen_outbound({"query": "天気", "history": [{"text": "連絡先：ｔｅｓｔ＠ｅｘａｍｐｌｅ．ｃｏｍ"}]}, judge)
    assert result.blocked and not judge.calls


def test_outbound_always_checks_context_even_without_keywords():
    judge = LocalJudge(0.5)
    payload = {"query": "例", "history": ["伏せておきたい話"]}
    assert guard.screen_outbound(payload, judge).review_required
    assert json.loads(judge.calls[0]["text"]) == payload


@pytest.mark.parametrize("probability,error", [(0.95, None), (0.4, None), (0.0, JevError("timeout"))])
def test_search_never_sends_when_blocked(monkeypatch, probability, error):
    monkeypatch.setenv("XAI_API_KEY", "test-only")
    monkeypatch.setattr(facts, "screen_outbound", lambda payload: guard.screen_outbound(payload, LocalJudge(probability, error)))
    monkeypatch.setattr(facts.requests, "post", lambda *args, **kwargs: pytest.fail("Unexpected external send"))
    assert facts.ask_grok_with_search("富士山の高さを確認") is None


def test_exact_request_body_checked_before_send(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "test-only")
    checked = []
    def inspect(payload):
        checked.append(json.loads(json.dumps(payload)))
        return guard.ScreenResult(False)
    def post(url, **kwargs):
        assert checked == [kwargs["json"]]
        return SimpleNamespace(status_code=200, json=lambda: {"output_text": "確認済み"})
    monkeypatch.setattr(facts, "screen_outbound", inspect)
    monkeypatch.setattr(facts.requests, "post", post)
    assert facts.ask_grok_with_search("富士山の高さを確認") == "確認済み"
