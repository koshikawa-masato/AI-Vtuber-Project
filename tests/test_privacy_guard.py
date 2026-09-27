from types import SimpleNamespace

import pytest

from src.line_bot_vps import privacy_guard as g


class FakeJev:
    def __init__(self, p=None, error=None):
        self.p, self.error, self.calls = p, error, []

    def evaluate_noul(self, state, questions):
        self.calls.append(state)
        if self.error:
            raise self.error
        return SimpleNamespace(probabilities={"sensitive": self.p})


@pytest.mark.parametrize("text,kind", [
    ("電話は090-1234-5678です", "電話番号"),
    ("09012345678にかけて", "電話番号"),
    ("+81 90 1234 5678", "電話番号"),
    ("メールはtaro.yamada@example.co.jpね", "メールアドレス"),
    ("〒100-0001に送って", "郵便番号"),
    ("東京都千代田区千代田1-1に住んでる", "住所"),
    ("カードは4111 1111 1111 1111", "カード番号"),
    ("番号は1234-5678-9012", "マイナンバー"),
])
def test_identifiers_are_redacted(text, kind):
    redacted, kinds = g.redact_identifiers(text)
    assert kinds == [kind]
    assert f"［{kind}］" in redacted
    assert "1234" not in redacted or kind == "住所"


@pytest.mark.parametrize("text", [
    "スイの大冒険は8巻まで出てる",
    "2026年9月25日にLTがある",
    "1234円だった",
    "富士山は3776mだよ",
    "カードは1234 5678 9012 3456",  # fails Luhn
    "配信は20時からだって",
])
def test_ordinary_numbers_are_kept(text):
    redacted, kinds = g.redact_identifiers(text)
    assert kinds == [] and redacted == text


def test_identifier_blocks_without_jev():
    jev = FakeJev(p=0.0)
    result = g.screen("連絡先は090-1234-5678", jev)
    assert result.blocked and result.kinds == ["電話番号"] and jev.calls == []


def test_clean_text_never_reaches_jev():
    jev = FakeJev(p=0.99)
    assert not g.screen("今日のお昼なに食べようかな", jev).blocked
    assert jev.calls == []


def test_keyword_goes_to_jev_and_jev_decides():
    assert g.screen("父が入院して手術することになったんだ", FakeJev(p=0.92)).blocked
    result = g.screen("病院が舞台のドラマ観てる", FakeJev(p=0.05))
    assert not result.blocked and result.how == "lev sensitive=0.05"


def test_jev_down_is_cautious_only_after_a_keyword():
    down = FakeJev(error=g.JevError("timeout"))
    assert g.screen("持病があって薬を飲んでる", down).blocked
    assert not g.screen("スバルの配信見た？", down).blocked


def test_notice_fills_placeholders(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "PROMPTS_DIR", tmp_path)
    (tmp_path / "privacy_notice_blocked.txt").write_text("{count}回目です（残り{remaining}回）", encoding="utf-8")
    assert g.notice("blocked", count=1, remaining=2) == "1回目です（残り2回）"
    assert g.notice("missing") == "[missing]"
