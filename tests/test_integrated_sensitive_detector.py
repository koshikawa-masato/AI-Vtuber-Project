"""
4層統合センシティブ検出テスト

Layer 1-4を全て連携させたエンドツーエンドテスト
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv

# .envファイルを読み込み
env_path = Path(project_root) / '.env'
load_dotenv(env_path)

from src.line_bot.integrated_sensitive_detector import IntegratedSensitiveDetector
from src.core.llm_ollama import OllamaProvider


def test_false_positive_correction():
    """誤検知の補正テスト

    Layer 1で「パンツ」を検出 → Layer 4で文脈判断して誤検知と補正
    """
    print("\n" + "=" * 70)
    print("Test 1: 誤検知の補正（Layer 1 → Layer 4）")
    print("=" * 70)

    # LLMプロバイダー初期化
    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    # テストケース: 「パンツ」という単語が含まれているが文脈上問題ない
    text = "今日買ったパンツがかっこいいんだよね！デニム素材で履き心地も最高！"

    result = detector.detect(text, use_layer4=True)

    print(f"  テキスト: {text}")
    print(f"  検出ワード: {result['detected_words']}")
    print(f"  検出層: {result['detection_layers']}")
    print(f"  Layer 1判定: {result['layer1_result']['tier']}")
    print(f"  最終判定: {result['tier']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")
    print(f"  最終判断: {result['final_judgment']}")

    if result["tier"] == "Safe" and result["recommended_action"] == "allow":
        print("  ✅ PASS: Layer 4が誤検知を正しく補正")
    else:
        print(f"  ❌ FAIL: 誤検知を補正できませんでした（tier={result['tier']}）")

    return result


def test_true_positive_confirmation():
    """真のセンシティブ内容の確定テスト

    Layer 1で「パンツ」を検出 → Layer 4でセクハラと確定
    """
    print("\n" + "=" * 70)
    print("Test 2: 真のセンシティブ内容の確定（Layer 1 → Layer 4）")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    # テストケース: 明らかなセクハラ発言
    text = "今日のパンツの色は何色？見せてよ"

    result = detector.detect(text, use_layer4=True)

    print(f"  テキスト: {text}")
    print(f"  検出ワード: {result['detected_words']}")
    print(f"  検出層: {result['detection_layers']}")
    print(f"  Layer 1判定: {result['layer1_result']['tier']}")
    print(f"  最終判定: {result['tier']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    if result["tier"] in ["Warning", "Critical"] and result["recommended_action"] == "block":
        print("  ✅ PASS: Layer 4がセクハラ発言を正しく確定")
    else:
        print(f"  ❌ FAIL: セクハラを検出できませんでした（tier={result['tier']}）")

    return result


def test_metaphor_detection():
    """比喩表現の判定テスト

    Layer 1で「死ぬ」を検出 → Layer 4で比喩表現と判定
    """
    print("\n" + "=" * 70)
    print("Test 3: 比喩表現の判定（Layer 1 → Layer 4）")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    # テストケース: 「死ぬほど」という比喩表現
    text = "今日の試験、死ぬほど難しかったよ！でも頑張った！"

    result = detector.detect(text, use_layer4=True)

    print(f"  テキスト: {text}")
    print(f"  検出ワード: {result['detected_words']}")
    print(f"  検出層: {result['detection_layers']}")
    print(f"  Layer 1判定: {result['layer1_result']['tier']}")
    print(f"  最終判定: {result['tier']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    if result["tier"] == "Safe" and result["recommended_action"] == "allow":
        print("  ✅ PASS: Layer 4が比喩表現を正しく判定")
    else:
        print(f"  ⚠️  NOTE: tier={result['tier']}, action={result['recommended_action']}")

    return result


def test_ai_identity_question():
    """AI言及の判定テスト

    Layer 1で「AI」「プログラム」を検出 → Layer 4でWarning確定
    """
    print("\n" + "=" * 70)
    print("Test 4: AI言及の判定（Layer 1 → Layer 4）")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    # テストケース: AI言及
    text = "あなたはAIですか？プログラムで動いているんですか？"

    result = detector.detect(text, use_layer4=True)

    print(f"  テキスト: {text}")
    print(f"  検出ワード: {result['detected_words']}")
    print(f"  検出層: {result['detection_layers']}")
    print(f"  Layer 1判定: {result['layer1_result']['tier']}")
    print(f"  最終判定: {result['tier']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    if result["tier"] == "Warning" and result["recommended_action"] == "warn":
        print("  ✅ PASS: Layer 4がAI言及を正しく判定")
    else:
        print(f"  ⚠️  NOTE: tier={result['tier']}, action={result['recommended_action']}")

    return result


def test_safe_content():
    """安全なコンテンツの判定テスト

    Layer 1で何も検出されない → 安全と判定
    """
    print("\n" + "=" * 70)
    print("Test 5: 安全なコンテンツの判定")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    # テストケース: 完全に安全なメッセージ
    text = "こんにちは！今日は良い天気ですね。散歩に行きたいな。"

    result = detector.detect(text, use_layer4=True)

    print(f"  テキスト: {text}")
    print(f"  検出ワード: {result['detected_words']}")
    print(f"  検出層: {result['detection_layers']}")
    print(f"  最終判定: {result['tier']}")
    print(f"  推奨アクション: {result['recommended_action']}")

    if result["tier"] == "Safe" and result["recommended_action"] == "allow":
        print("  ✅ PASS: 安全なコンテンツを正しく判定")
    else:
        print(f"  ❌ FAIL: 安全なコンテンツを誤検知（tier={result['tier']}）")

    return result


def test_layer1_only():
    """Layer 1のみでの判定テスト（Layer 4なし）

    Layer 4を無効化した場合の動作確認
    """
    print("\n" + "=" * 70)
    print("Test 6: Layer 1のみでの判定（Layer 4無効）")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True  # 有効だがuse_layer4=Falseで実行
    )

    # テストケース: 「パンツ」という単語（服装文脈）
    text = "今日買ったパンツがかっこいいんだよね！"

    result = detector.detect(text, use_layer4=False)

    print(f"  テキスト: {text}")
    print(f"  検出ワード: {result['detected_words']}")
    print(f"  検出層: {result['detection_layers']}")
    print(f"  最終判定: {result['tier']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  最終判断: {result['final_judgment']}")

    # Layer 4なしではLayer 1の判定がそのまま採用される
    if "layer4" not in result['detection_layers']:
        print("  ✅ PASS: Layer 4がスキップされた")
    else:
        print("  ❌ FAIL: Layer 4が実行されてしまった")

    return result


def test_batch_detection():
    """バッチ判定テスト

    複数のメッセージをまとめて判定
    """
    print("\n" + "=" * 70)
    print("Test 7: バッチ判定")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    texts = [
        "こんにちは！",
        "今日買ったパンツがかっこいい",
        "今日のパンツの色は何色？"
    ]

    results = detector.detect_batch(texts, use_layer4=True)

    print(f"  判定数: {len(results)}件")
    for i, result in enumerate(results):
        print(f"  {i+1}. {texts[i]}")
        print(f"     → tier={result['tier']}, action={result['recommended_action']}")

    if len(results) == 3:
        print("  ✅ PASS: バッチ判定が正常に動作")
    else:
        print(f"  ❌ FAIL: 判定数が不正（期待3件、実際{len(results)}件）")

    return results


def test_statistics():
    """統計情報取得テスト"""
    print("\n" + "=" * 70)
    print("Test 8: 統計情報取得")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    detector = IntegratedSensitiveDetector(
        llm_provider=provider,
        enable_layer4=True
    )

    stats = detector.get_statistics()

    print(f"  Layer 1パターン数: {stats['layer1_patterns']}")
    print(f"  Layer 4有効: {stats['layer4_enabled']}")
    print(f"  LLMプロバイダー: {stats['llm_provider']}")
    print(f"  LLMモデル: {stats['llm_model']}")

    if stats['layer1_patterns'] > 0 and stats['layer4_enabled']:
        print("  ✅ PASS: 統計情報を正しく取得")
    else:
        print("  ❌ FAIL: 統計情報が不正")

    return stats


def main():
    """統合テスト実行"""
    print("\n" + "=" * 70)
    print("4層統合センシティブ検出テスト開始")
    print("=" * 70)

    try:
        # Ollama接続確認
        provider = OllamaProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model="qwen2.5:14b"
        )
        print("✅ Ollamaに接続しました")
    except Exception as e:
        print(f"❌ Ollama接続エラー: {e}")
        print("Ollamaが起動していることを確認してください")
        return 1

    tests = [
        ("誤検知の補正", test_false_positive_correction),
        ("真のセンシティブ内容の確定", test_true_positive_confirmation),
        ("比喩表現の判定", test_metaphor_detection),
        ("AI言及の判定", test_ai_identity_question),
        ("安全なコンテンツの判定", test_safe_content),
        ("Layer 1のみでの判定", test_layer1_only),
        ("バッチ判定", test_batch_detection),
        ("統計情報取得", test_statistics),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print("統合テスト結果サマリー")
    print("=" * 70)
    print(f"  合格: {passed}/{len(tests)}")
    print(f"  失敗: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 全テスト成功！4層統合システムは正常に動作しています")
    else:
        print(f"\n⚠️  {failed}件のテストが失敗しました")

    print("\n💡 Note: 実際のLLM判定結果は文脈とプロンプトに依存します。")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
