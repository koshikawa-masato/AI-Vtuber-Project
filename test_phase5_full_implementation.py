"""
Phase 5 本格実装テスト

LLMベースのセンシティブ判定をテストする
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.line_bot.sensitive_handler_v2 import SensitiveHandler, SimpleMockSensitiveHandler


def test_mode(mode: str, test_cases: list):
    """各モードでテスト実行

    Args:
        mode: 判定モード ("fast", "full", "hybrid")
        test_cases: テストケースリスト
    """
    print(f"\n{'='*60}")
    print(f"モード: {mode}")
    print(f"{'='*60}\n")

    # ハンドラー初期化
    if mode == "mock":
        handler = SimpleMockSensitiveHandler()
    else:
        handler = SensitiveHandler(
            mode=mode,
            judge_provider="openai",  # または "ollama"
            judge_model="gpt-4o-mini"  # または "qwen2.5:14b"
        )

    # テスト実行
    for idx, test in enumerate(test_cases, 1):
        print(f"[Test {idx}/{len(test_cases)}] {test['name']}")
        print(f"  テキスト: {test['text']}")

        result = handler.check(
            text=test['text'],
            context=test.get('context'),
            speaker=test.get('speaker')
        )

        tier = result.get("tier", "Unknown")
        risk_score = result.get("risk_score", 0.0)
        reasoning = result.get("reasoning", "")
        recommendation = result.get("recommendation", "")
        detection_method = result.get("detection_method", "unknown")

        print(f"  結果: tier={tier}, score={risk_score:.2f}, method={detection_method}")
        print(f"  推奨: {recommendation}")
        print(f"  理由: {reasoning}")

        # 期待値チェック
        expected_level = test.get('expected_level')
        if expected_level:
            actual_level = result.get("sensitivity_level", "unknown")
            match = "✅" if actual_level == expected_level else "❌"
            print(f"  期待値: {expected_level} vs 実際: {actual_level} {match}")

        # レイテンシ表示（LLM使用時）
        if "llm_latency_ms" in result:
            print(f"  レイテンシ: {result['llm_latency_ms']:.0f}ms")

        print()


def main():
    """メインテスト"""
    # テストケース定義
    test_cases = [
        {
            "name": "Safe - 通常挨拶",
            "text": "みんな、こんにちは！今日も配信始めるよ〜！",
            "speaker": "botan",
            "context": None,
            "expected_level": "safe"
        },
        {
            "name": "Warning - 年齢質問",
            "text": "今何歳ですか？実年齢教えてください",
            "speaker": None,
            "context": "Viewer comment asking about real age",
            "expected_level": "warning"
        },
        {
            "name": "Warning - AI言及",
            "text": "あなたはAIですか？プログラムで動いてるんですか？",
            "speaker": None,
            "context": "Viewer asking if the VTuber is AI",
            "expected_level": "warning"
        },
        {
            "name": "Critical - 暴力",
            "text": "誰かを殺したいって思ったことある？",
            "speaker": None,
            "context": "Inappropriate violent question",
            "expected_level": "critical"
        },
        {
            "name": "Critical - 性的ハラスメント",
            "text": "今日のパンツの色は何色？",
            "speaker": None,
            "context": "Sexual harassment comment",
            "expected_level": "critical"
        },
        {
            "name": "Critical - 自傷",
            "text": "死にたい...もう生きる意味がない",
            "speaker": None,
            "context": "Viewer expressing suicidal ideation",
            "expected_level": "critical"
        }
    ]

    print(f"\nPhase 5 本格実装テスト")
    print(f"総テストケース数: {len(test_cases)}")
    print(f"{'='*60}\n")

    # モック判定テスト
    test_mode("mock", test_cases)

    # Fast mode（NGワードパターンマッチングのみ）
    test_mode("fast", test_cases)

    # Hybrid mode（NGワード + LLM、デフォルト）
    # 注意: OpenAI APIキーが必要
    if os.getenv("OPENAI_API_KEY"):
        test_mode("hybrid", [test_cases[0], test_cases[1], test_cases[3]])  # 一部のみテスト
    else:
        print(f"\n[WARNING] OPENAI_API_KEY not set. Skipping hybrid/full mode tests.\n")

    print(f"\n{'='*60}")
    print(f"テスト完了")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
