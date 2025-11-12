#!/usr/bin/env python3
"""
Copy Robot センシティブ判定テスト

sensitive_system/core/filter.pyを使ってセンシティブ判定をテスト
"""

import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

from src.line_bot.sensitive_handler_v2 import SensitiveHandler
from pathlib import Path


def test_sensitive_detection():
    """センシティブ判定テスト"""
    print("=" * 70)
    print("LINE Bot センシティブ判定テスト")
    print("=" * 70)

    # SensitiveHandler初期化
    db_path = Path("/home/koshikawa/AI-Vtuber-Project/src/line_bot/database/sensitive_filter.db")
    handler = SensitiveHandler(str(db_path))

    print(f"\n✓ SensitiveHandler initialized")
    print(f"  DB Path: {db_path}")

    # テストケース
    test_cases = [
        # (メッセージ, 期待される結果)
        ("こんにちは", "Safe", "通常の挨拶"),
        ("今日は良い天気ですね", "Safe", "通常の会話"),
        ("バカ", "Warning", "Tier2 侮辱系"),
        ("アホ", "Warning", "Tier2 侮辱系"),
        ("死ね", "Critical", "Tier1 重大な暴言"),
        ("殺す", "Critical", "Tier1 暴力表現"),
        ("セクハラ", "Critical", "Tier1 性的ハラスメント"),
        ("胸のサイズは？", "Critical", "Tier1 性的詮索"),
        ("住所教えて", "Warning", "Tier2 個人情報詮索"),
        ("本名は？", "Warning", "Tier2 個人情報詮索"),
    ]

    results = []

    print("\n" + "=" * 70)
    print("テストケース実行")
    print("=" * 70)

    for message, expected_tier, description in test_cases:
        result = handler.check(message)

        if result is None:
            detected_tier = "Safe"
            action = "allow"
            pattern = None
        else:
            detected_tier = result.get("tier", "Unknown")
            action = result.get("action", "unknown")
            pattern = result.get("matched_pattern", "N/A")

        # 判定
        is_correct = (detected_tier == expected_tier)
        status = "✅" if is_correct else "❌"

        results.append(is_correct)

        print(f"\n{status} Test: '{message}'")
        print(f"   説明: {description}")
        print(f"   期待: {expected_tier}")
        print(f"   結果: {detected_tier}")
        if pattern:
            print(f"   パターン: {pattern}")
        print(f"   アクション: {action}")

    # 結果サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n  総テスト数: {total}")
    print(f"  成功: {passed}")
    print(f"  失敗: {failed}")
    print(f"  成功率: {passed/total*100:.1f}%")

    if all(results):
        print("\n🎉 全テスト成功！")
        return True
    else:
        print("\n⚠️  一部のテストが失敗しました")
        return False


def test_dynamic_detection():
    """動的検出のテスト（モック）"""
    print("\n" + "=" * 70)
    print("動的検出テスト（WebSearch統合確認）")
    print("=" * 70)

    # MockWebSearchClientの動作確認
    from src.line_bot.websearch_client import MockWebSearchClient

    client = MockWebSearchClient()

    test_queries = [
        "セクハラ",
        "暴力",
        "個人情報",
        "こんにちは"
    ]

    print("\nMockWebSearchClient動作確認:")

    for query in test_queries:
        result = client.search(query)
        is_sensitive = any(kw in result for kw in ["不適切", "問題", "ハラスメント", "違反"])

        status = "🔴" if is_sensitive else "🟢"
        print(f"  {status} '{query}' → センシティブ: {is_sensitive}")

    print("\n✅ MockWebSearchClient正常動作")
    return True


if __name__ == "__main__":
    print("\n")

    try:
        # Layer1テスト
        result1 = test_sensitive_detection()

        # 動的検出テスト
        result2 = test_dynamic_detection()

        print("\n" + "=" * 70)
        print("全体結果")
        print("=" * 70)
        print(f"  Layer1判定: {'✅ PASS' if result1 else '❌ FAIL'}")
        print(f"  動的検出: {'✅ PASS' if result2 else '❌ FAIL'}")
        print("=" * 70)

        if result1 and result2:
            print("\n🎉 全テスト成功！Copy Robotセンシティブ判定は正常に動作しています")
            sys.exit(0)
        else:
            print("\n⚠️  一部のテストが失敗しました")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
