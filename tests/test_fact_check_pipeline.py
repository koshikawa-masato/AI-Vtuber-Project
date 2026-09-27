from types import SimpleNamespace

import pytest

from src.line_bot_vps import fact_check_pipeline as f


class FakeJev:
    def __init__(self, answers=None, error=None):
        self.answers, self.error, self.calls = answers or {}, error, []

    def evaluate_noul(self, state, questions):
        self.calls.append((state, questions))
        if self.error:
            raise self.error
        return SimpleNamespace(probabilities={k: self.answers[k] for k in questions})


@pytest.fixture(autouse=True)
def prompt_file(tmp_path, monkeypatch):
    (tmp_path / f.PROMPT_FILE).write_text("検証して: {statement}", encoding="utf-8")
    monkeypatch.setattr(f, "PROMPTS_DIR", tmp_path)


def never_called(question, use_x):
    raise AssertionError("Grok must not be called")


@pytest.fixture(autouse=True)
def empty_memory(monkeypatch):
    # Tests never touch the real DB; individual tests pass lookup= when memory matters.
    monkeypatch.setattr(f, "lookup_known_facts", lambda statement: [])


SUI = [{"word": "スイの大冒険", "meaning": "双葉ももが作画、江口連が原作のスピンオフ漫画。", "similarity": 0.64}]


def test_memory_settles_the_statement_without_grok():
    jev = FakeJev({"checkable": 0.9, "supported": 0.95, "refuted": 0.02})
    result = f.run_fact_check("スイの大冒険の作画は双葉もも", client=jev, ask=never_called, lookup=lambda s: SUI)
    assert result["passed"] is True and result["source"] == "memory" and result["confidence"] == 0.85
    wrong = FakeJev({"checkable": 0.9, "supported": 0.02, "refuted": 0.93})
    result = f.run_fact_check("スイの大冒険の作画は鳥山明", client=wrong, ask=never_called, lookup=lambda s: SUI)
    assert result["passed"] is False and result["confidence"] == 0.0 and "双葉もも" in result["correct_info"]


def test_memory_that_does_not_settle_it_goes_to_grok():
    jev = FakeJev({"checkable": 0.9, "supported": 0.2, "refuted": 0.1})
    asked = []
    f.run_fact_check("スイの大冒険は10巻まで出ている", client=jev, lookup=lambda s: SUI,
                     ask=lambda q, x: asked.append(q) or "不明")
    assert len(asked) == 1


def test_personal_statement_never_reaches_memory_or_grok():
    def no_lookup(statement):
        raise AssertionError("memory lookup must not run")
    f.run_fact_check("私は青が好き", client=FakeJev({"checkable": 0.05}), ask=never_called, lookup=no_lookup)


def test_personal_statement_skips_grok():
    jev = FakeJev({"checkable": 0.06})
    result = f.run_fact_check("私は青が好き", client=jev, ask=never_called)
    assert result["passed"] is True and result["source"] == "jev_gate"


def test_uncertain_gate_does_not_spend_on_grok():
    result = f.run_fact_check("来月なにか出るらしい", client=FakeJev({"checkable": 0.5}), ask=never_called)
    assert result["passed"] is False and result["confidence"] == 0.5 and result["source"] == "jev_gate"


def test_gate_threshold_is_configurable(monkeypatch):
    monkeypatch.setenv("GROK_GATE_MIN_PROBABILITY", "0.4")
    jev = FakeJev({"checkable": 0.5, "supported": 0.9, "refuted": 0.02})
    assert f.run_fact_check("富士山は3776m", client=jev, ask=lambda q, x: "正しい")["source"] == "grok"


def test_confident_gate_checks_and_supported_verdict_passes():
    jev = FakeJev({"checkable": 0.95, "supported": 0.93, "refuted": 0.03})
    asked = []
    result = f.run_fact_check("富士山は3776m", client=jev, ask=lambda q, x: asked.append((q, x)) or "その通りです。")
    assert asked == [("検証して: 富士山は3776m", True)]
    assert result == {"passed": True, "confidence": 0.9, "verification": "その通りです。", "source": "grok"}


def test_refuted_verdict_blocks_with_zero_confidence():
    jev = FakeJev({"checkable": 0.95, "supported": 0.05, "refuted": 0.9})
    result = f.run_fact_check("富士山は5000m", client=jev, ask=lambda q, x: "間違い: 正しくは3776mです")
    assert result["passed"] is False and result["confidence"] == 0.0
    assert result["correct_info"] == "3776mです"


def test_correct_info_drops_markdown_bold():
    assert f.extract_correct_info("**間違い: 正しくは3776m**\n\n根拠...") == "3776m"


def test_unclear_verdict_is_unknown():
    jev = FakeJev({"checkable": 0.9, "supported": 0.4, "refuted": 0.35})
    result = f.run_fact_check("来月新曲が出るらしい", client=jev, ask=lambda q, x: "確認できる情報は見つかりませんでした。")
    assert result["passed"] is False and result["confidence"] == 0.5


def test_grok_failure_is_unknown_not_a_pass():
    jev = FakeJev({"checkable": 0.9})
    result = f.run_fact_check("富士山は3776m", client=jev, ask=lambda q, x: None)
    assert result == {"passed": False, "confidence": 0.5, "verification": "Grok API呼び出し失敗", "source": "grok"}


def test_jev_down_means_no_grok_and_unverified():
    jev = FakeJev(error=f.JevError("timeout"))
    result = f.run_fact_check("富士山は3776m", client=jev, ask=never_called)
    assert result["passed"] is False and result["confidence"] == 0.5 and "jev_unavailable" in result["verification"]


def test_verdict_falls_back_to_keywords_when_jev_is_down():
    jev = FakeJev(error=f.JevError("timeout"))
    assert f.read_verdict("富士山は3776m", "正しい", jev)[0] is True
    assert f.read_verdict("富士山は5000m", "間違い: 正しくは3776m", jev)[0] is False


def test_extracts_text_from_responses_api_shapes():
    assert f.extract_response_text({"output_text": " はい "}) == "はい"
    nested = {"output": [{"type": "web_search_call"},
                         {"type": "message", "content": [{"type": "output_text", "text": "正しい"}]}]}
    assert f.extract_response_text(nested) == "正しい"
    assert f.extract_response_text({"output": []}) == ""
