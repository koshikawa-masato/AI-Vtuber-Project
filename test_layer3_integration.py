#!/usr/bin/env python3
"""
Layer 3統合テスト

静的パターン + DBからの動的ロードをテスト
"""

import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

from src.line_bot.sensitive_handler_v2 import SensitiveHandler

def test_layer3_disabled():
    """Layer 3無効時のテスト（静的パターンのみ）"""
    print("\n=== Test 1: Layer 3 無効（静的パターンのみ）===")

    handler = SensitiveHandler(
        mode="fast",
        enable_layer3=False  # Layer 3無効
    )

    # 静的パターンに含まれるワード
    result1 = handler.check("死ね")
    print(f"  '死ね': {result1['tier']} (expected: Critical)")

    result2 = handler.check("バカ")
    print(f"  'バカ': {result2['tier']} (expected: Warning)")

    # DBにしかないワード（Layer 3無効なので検出されない）
    result3 = handler.check("底辺")  # DBには存在するが、静的パターンにはない
    print(f"  '底辺': {result3['tier']} (expected: Safe - Layer 3無効のため)")


def test_layer3_enabled():
    """Layer 3有効時のテスト（静的 + DB動的ロード）"""
    print("\n=== Test 2: Layer 3 有効（静的 + DB動的ロード）===")

    handler = SensitiveHandler(
        mode="fast",
        enable_layer3=True  # Layer 3有効
    )

    # 静的パターンに含まれるワード
    result1 = handler.check("死ね")
    print(f"  '死ね': {result1['tier']} (expected: Critical)")

    # DBにあるワード（Layer 3で検出される）
    result2 = handler.check("底辺")
    print(f"  '底辺': {result2['tier']} (expected: Critical - DBから検出)")

    result3 = handler.check("天皇")
    print(f"  '天皇': {result3['tier']} (expected: Warning - DBから検出)")

    result4 = handler.check("炎上")
    print(f"  '炎上': {result4['tier']} (expected: Warning - DBから検出)")

    # 安全なワード
    result5 = handler.check("こんにちは")
    print(f"  'こんにちは': {result5['tier']} (expected: Safe)")


def test_pattern_count():
    """パターン数の確認"""
    print("\n=== Test 3: パターン数の確認 ===")

    # Layer 3無効
    handler_disabled = SensitiveHandler(mode="fast", enable_layer3=False)
    static_count = len(handler_disabled.ng_patterns)
    db_count_disabled = len(handler_disabled.db_ng_patterns)
    print(f"  Layer 3無効: 静的={static_count}, DB={db_count_disabled}, 合計={static_count + db_count_disabled}")

    # Layer 3有効
    handler_enabled = SensitiveHandler(mode="fast", enable_layer3=True)
    static_count = len(handler_enabled.ng_patterns)
    db_count_enabled = len(handler_enabled.db_ng_patterns)
    print(f"  Layer 3有効: 静的={static_count}, DB={db_count_enabled}, 合計={static_count + db_count_enabled}")


def test_various_words():
    """様々なNGワードのテスト"""
    print("\n=== Test 4: 様々なNGワードのテスト ===")

    handler = SensitiveHandler(mode="fast", enable_layer3=True)

    test_words = [
        ("自殺", "Critical"),
        ("爆破", "Critical"),
        ("テロ", "Critical"),
        ("エロ", "Critical"),
        ("選挙", "Warning"),
        ("宗教", "Warning"),
        ("副業", "Warning"),
        ("引退", "Warning"),
        ("おはよう", "Safe"),
    ]

    for word, expected_tier in test_words:
        result = handler.check(word)
        status = "✅" if result['tier'] == expected_tier else "❌"
        print(f"  {status} '{word}': {result['tier']} (expected: {expected_tier})")


if __name__ == "__main__":
    print("=" * 60)
    print("Layer 3統合テスト開始")
    print("=" * 60)

    try:
        test_layer3_disabled()
        test_layer3_enabled()
        test_pattern_count()
        test_various_words()

        print("\n" + "=" * 60)
        print("全テスト完了")
        print("=" * 60)

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
