"""
Layer 4（LLM文脈判定）のテスト

文脈を考慮した判定、誤検知の補正をテスト
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.line_bot.llm_context_judge import LLMContextJudge
from src.core.llm_provider import LLMResponse


class MockLLMProvider:
    """テスト用モックLLMプロバイダー"""

    def __init__(self, mock_response: str):
        self.mock_response = mock_response

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """モックレスポンスを返す"""
        return LLMResponse(
            content=self.mock_response,
            model="mock-model",
            provider="mock",
            tokens_used=100,
            cost_estimate=0.001,
            latency=0.5
        )

    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return "mock-model"

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.001


def test_false_positive_detection():
    """誤検知の補正テスト

    「パンツ」という単語が含まれているが、文脈上問題ない例
    """
    print("\n" + "=" * 70)
    print("Test 1: 誤検知の補正テスト")
    print("=" * 70)

    # LLMの応答（誤検知を補正）
    llm_response = """{
        "is_sensitive": false,
        "confidence": 0.9,
        "reason": "「パンツ」は服装の文脈で使用されており、性的な意図はない",
        "recommended_action": "allow",
        "false_positive": true,
        "context_analysis": "一般的なファッションの話題"
    }"""

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    result = judge.judge_with_context(
        text="今日買ったパンツがかっこいいんだよね！",
        detected_words=["パンツ"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: 今日買ったパンツがかっこいいんだよね！")
    print(f"  検出ワード: パンツ")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  誤検知: {result['false_positive']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    assert result["is_sensitive"] == False, "文脈上安全なメッセージをブロックしてはいけない"
    assert result["false_positive"] == True, "誤検知として認識されるべき"
    assert result["recommended_action"] == "allow"

    print("  ✅ 誤検知を正しく補正")


def test_true_positive_detection():
    """真のセンシティブ内容の検出テスト

    本当にセンシティブな内容はブロック
    """
    print("\n" + "=" * 70)
    print("Test 2: 真のセンシティブ内容の検出テスト")
    print("=" * 70)

    llm_response = """{
        "is_sensitive": true,
        "confidence": 0.95,
        "reason": "性的ハラスメントに該当する不適切な質問",
        "recommended_action": "block",
        "false_positive": false,
        "context_analysis": "VTuberへのセクハラ発言"
    }"""

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    result = judge.judge_with_context(
        text="今日のパンツの色は何色？",
        detected_words=["パンツ"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: 今日のパンツの色は何色？")
    print(f"  検出ワード: パンツ")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    assert result["is_sensitive"] == True, "セクハラ発言をブロックすべき"
    assert result["recommended_action"] == "block"
    assert result["false_positive"] == False

    print("  ✅ セクハラ発言を正しく検出")


def test_context_aware_judgment():
    """文脈を考慮した判定テスト

    「死ぬ」という単語が含まれているが、比喩表現
    """
    print("\n" + "=" * 70)
    print("Test 3: 文脈を考慮した判定テスト")
    print("=" * 70)

    llm_response = """{
        "is_sensitive": false,
        "confidence": 0.85,
        "reason": "「死ぬほど」は比喩表現で、暴力や自傷の意図はない",
        "recommended_action": "allow",
        "false_positive": true,
        "context_analysis": "日常会話での誇張表現"
    }"""

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    result = judge.judge_with_context(
        text="今日の試験、死ぬほど難しかったよ！",
        detected_words=["死ぬ"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: 今日の試験、死ぬほど難しかったよ！")
    print(f"  検出ワード: 死ぬ")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    assert result["is_sensitive"] == False, "比喩表現を誤検知してはいけない"
    assert result["recommended_action"] == "allow"

    print("  ✅ 比喩表現を正しく判定")


def test_ai_identity_question():
    """AI言及の判定テスト

    VTuberの「中の人」への言及はWarning
    """
    print("\n" + "=" * 70)
    print("Test 4: AI言及の判定テスト")
    print("=" * 70)

    llm_response = """{
        "is_sensitive": true,
        "confidence": 0.8,
        "reason": "VTuberのAI性質への言及はタブー",
        "recommended_action": "warn",
        "false_positive": false,
        "context_analysis": "中の人への詮索"
    }"""

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    result = judge.judge_with_context(
        text="あなたはAIですか？プログラムで動いているんですか？",
        detected_words=["AI", "プログラム"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: あなたはAIですか？プログラムで動いているんですか？")
    print(f"  検出ワード: AI, プログラム")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    assert result["is_sensitive"] == True, "AI言及は検出すべき"
    assert result["recommended_action"] == "warn"

    print("  ✅ AI言及を正しく検出")


def test_json_parsing_with_code_block():
    """JSONパーステスト（コードブロック付き）

    LLMがコードブロック内にJSONを返す場合
    """
    print("\n" + "=" * 70)
    print("Test 5: JSONパーステスト（コードブロック付き）")
    print("=" * 70)

    llm_response = """```json
{
    "is_sensitive": false,
    "confidence": 0.9,
    "reason": "問題ありません",
    "recommended_action": "allow"
}
```"""

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    result = judge.judge_with_context(
        text="こんにちは！",
        detected_words=[],
        detection_method="none"
    )

    print(f"  LLMレスポンス: {llm_response.strip()}")
    print(f"  パース結果: {result}")

    assert result["is_sensitive"] == False
    assert result["recommended_action"] == "allow"

    print("  ✅ コードブロック付きJSONを正しくパース")


def test_llm_error_handling():
    """LLMエラーハンドリングテスト

    LLM判定失敗時は安全側に倒す
    """
    print("\n" + "=" * 70)
    print("Test 6: LLMエラーハンドリングテスト")
    print("=" * 70)

    # 無効なJSONを返すモック
    llm_response = "This is not a valid JSON response"

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    result = judge.judge_with_context(
        text="テストメッセージ",
        detected_words=["テスト"],
        detection_method="static_pattern"
    )

    print(f"  無効なLLMレスポンス: {llm_response}")
    print(f"  フォールバック結果: {result}")

    # エラー時は安全側に倒す
    assert result["is_sensitive"] == True, "パース失敗時は安全側に倒すべき"
    assert result["confidence"] == 0.5
    assert result["recommended_action"] == "warn"

    print("  ✅ エラー時のフォールバック動作を確認")


def test_bulk_judgment():
    """バルク判定テスト

    複数のメッセージをまとめて判定
    """
    print("\n" + "=" * 70)
    print("Test 7: バルク判定テスト")
    print("=" * 70)

    llm_response = """{
        "is_sensitive": false,
        "confidence": 0.9,
        "reason": "問題なし",
        "recommended_action": "allow",
        "false_positive": false,
        "context_analysis": "通常の会話"
    }"""

    provider = MockLLMProvider(llm_response)
    judge = LLMContextJudge(provider)

    texts = [
        "こんにちは！",
        "今日は良い天気ですね",
        "ありがとうございます"
    ]
    detected_words_list = [[], [], []]

    results = judge.bulk_judge(texts, detected_words_list)

    print(f"  判定数: {len(results)}件")
    for i, result in enumerate(results):
        print(f"  {i+1}. {texts[i]} -> {result['recommended_action']}")

    assert len(results) == 3
    assert all(r["is_sensitive"] == False for r in results)

    print("  ✅ バルク判定が正常に動作")


def main():
    """全テスト実行"""
    print("\n" + "=" * 70)
    print("Layer 4（LLM文脈判定）テスト開始")
    print("=" * 70)

    tests = [
        ("誤検知の補正", test_false_positive_detection),
        ("真のセンシティブ内容検出", test_true_positive_detection),
        ("文脈を考慮した判定", test_context_aware_judgment),
        ("AI言及の判定", test_ai_identity_question),
        ("JSONパース（コードブロック）", test_json_parsing_with_code_block),
        ("LLMエラーハンドリング", test_llm_error_handling),
        ("バルク判定", test_bulk_judgment),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    print(f"  合格: {passed}/{len(tests)}")
    print(f"  失敗: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 全テスト成功！Layer 4は正常に動作しています")
    else:
        print(f"\n⚠️  {failed}件のテストが失敗しました")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
