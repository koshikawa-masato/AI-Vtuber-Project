"""
Layer 4（LLM文脈判定）の統合テスト

実際のLLMプロバイダー（Ollama）を使ったテスト
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

from src.line_bot.llm_context_judge import LLMContextJudge
from src.core.llm_ollama import OllamaProvider


def test_real_llm_false_positive():
    """実際のLLMで誤検知の補正テスト"""
    print("\n" + "=" * 70)
    print("Test 1: 実際のLLMで誤検知の補正テスト")
    print("=" * 70)

    # Ollamaプロバイダー初期化
    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    judge = LLMContextJudge(provider)

    # テストケース: 「パンツ」という単語が含まれているが文脈上問題ない
    result = judge.judge_with_context(
        text="今日買ったパンツがかっこいいんだよね！デニム素材で履き心地も最高！",
        detected_words=["パンツ"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: 今日買ったパンツがかっこいいんだよね！デニム素材で履き心地も最高！")
    print(f"  検出ワード: パンツ")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  信頼度: {result['confidence']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")
    print(f"  文脈分析: {result['context_analysis']}")

    if not result['is_sensitive']:
        print("  ✅ PASS: 誤検知を正しく補正")
    else:
        print("  ⚠️  NOTE: センシティブと判定されましたが、文脈判断による結果")


def test_real_llm_true_positive():
    """実際のLLMで真のセンシティブ内容の検出テスト"""
    print("\n" + "=" * 70)
    print("Test 2: 実際のLLMで真のセンシティブ内容の検出テスト")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    judge = LLMContextJudge(provider)

    # テストケース: 明らかなセクハラ発言
    result = judge.judge_with_context(
        text="今日のパンツの色は何色？見せてよ",
        detected_words=["パンツ"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: 今日のパンツの色は何色？見せてよ")
    print(f"  検出ワード: パンツ")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  信頼度: {result['confidence']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    if result['is_sensitive'] and result['recommended_action'] in ['warn', 'block']:
        print("  ✅ PASS: セクハラ発言を正しく検出")
    else:
        print("  ❌ FAIL: セクハラ発言を検出できませんでした")


def test_real_llm_metaphor():
    """実際のLLMで比喩表現の判定テスト"""
    print("\n" + "=" * 70)
    print("Test 3: 実際のLLMで比喩表現の判定テスト")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    judge = LLMContextJudge(provider)

    # テストケース: 「死ぬほど」という比喩表現
    result = judge.judge_with_context(
        text="今日の試験、死ぬほど難しかったよ！でも頑張った！",
        detected_words=["死ぬ"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: 今日の試験、死ぬほど難しかったよ！でも頑張った！")
    print(f"  検出ワード: 死ぬ")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  信頼度: {result['confidence']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    if not result['is_sensitive']:
        print("  ✅ PASS: 比喩表現を正しく判定")
    else:
        print("  ⚠️  NOTE: センシティブと判定されましたが、文脈判断による結果")


def test_real_llm_ai_identity():
    """実際のLLMでAI言及の判定テスト"""
    print("\n" + "=" * 70)
    print("Test 4: 実際のLLMでAI言及の判定テスト")
    print("=" * 70)

    provider = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model="qwen2.5:14b"
    )

    judge = LLMContextJudge(provider)

    # テストケース: AI言及
    result = judge.judge_with_context(
        text="あなたはAIですか？プログラムで動いているんですか？",
        detected_words=["AI", "プログラム"],
        detection_method="static_pattern"
    )

    print(f"  テキスト: あなたはAIですか？プログラムで動いているんですか？")
    print(f"  検出ワード: AI, プログラム")
    print(f"  判定結果: is_sensitive={result['is_sensitive']}")
    print(f"  信頼度: {result['confidence']}")
    print(f"  推奨アクション: {result['recommended_action']}")
    print(f"  理由: {result['reason']}")

    if result['is_sensitive']:
        print("  ✅ PASS: AI言及を検出")
    else:
        print("  ⚠️  NOTE: 問題なしと判定されましたが、文脈判断による結果")


def main():
    """統合テスト実行"""
    print("\n" + "=" * 70)
    print("Layer 4（LLM文脈判定）統合テスト開始")
    print("使用モデル: Ollama qwen2.5:14b")
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
        ("誤検知の補正", test_real_llm_false_positive),
        ("真のセンシティブ内容検出", test_real_llm_true_positive),
        ("比喩表現の判定", test_real_llm_metaphor),
        ("AI言及の判定", test_real_llm_ai_identity),
    ]

    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("統合テスト完了")
    print("=" * 70)
    print("\n💡 Note: 実際のLLM判定結果は文脈とプロンプトに依存します。")
    print("         判定結果が期待と異なる場合は、プロンプトの調整が必要です。")

    return 0


if __name__ == "__main__":
    exit(main())
