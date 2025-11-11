#!/usr/bin/env python3
"""
Layer 3 管理エンドポイントのテスト

拡張1: 新しいNGワードの追加とリロードのテスト
"""

import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

from src.line_bot.sensitive_handler_v2 import SensitiveHandler
from src.line_bot.dynamic_detector import DynamicSensitiveDetector
import sqlite3
from pathlib import Path

def test_add_and_reload():
    """NGワードをDBに追加してリロードするテスト"""
    print("\n=== Test: NGワード追加とリロード ===")

    # Layer 3有効でハンドラ初期化
    handler = SensitiveHandler(mode="fast", enable_layer3=True)

    # 初期状態のパターン数
    initial_count = len(handler.db_ng_patterns)
    print(f"  初期DBパターン数: {initial_count}")

    # DBに新しいNGワードを追加
    db_path = Path(__file__).parent / "src" / "line_bot" / "database" / "sensitive_filter.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    test_word = "テストNG単語"

    # 既存チェック
    cursor.execute("SELECT word_id FROM ng_words WHERE word = ?", (test_word,))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO ng_words
            (word, category, subcategory, severity, language, pattern_type,
             action, added_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_word, "tier2_general", "test", 6, "ja", "partial",
              "warn", "test_script", "テスト用NGワード"))
        conn.commit()
        print(f"  ✅ DBに追加: '{test_word}'")
    else:
        print(f"  ⚠️  既に存在: '{test_word}'")

    conn.close()

    # リロードを実行
    new_count = handler.reload_ng_words()
    print(f"  リロード後DBパターン数: {new_count}")

    # 新しいワードが検出されるかテスト
    result = handler.check(test_word)
    detected = result['tier'] != 'Safe' and len(result.get('matched_patterns', [])) > 0
    print(f"  '{test_word}' 検出テスト: tier={result['tier']}, patterns={len(result.get('matched_patterns', []))}")

    if detected:
        print("  ✅ 追加したNGワードが正常に検出されました")
    else:
        print("  ❌ 追加したNGワードが検出されませんでした")

    return detected


def test_immediate_reflection():
    """即座反映のテスト"""
    print("\n=== Test: 即座反映 ===")

    handler = SensitiveHandler(mode="fast", enable_layer3=True)

    # 安全なテキストで確認
    safe_text = "これは安全なメッセージです"
    result1 = handler.check(safe_text)
    print(f"  安全なテキスト: {result1['tier']}")

    # DBに新しいNGワードを追加（"緊急追加ワード"）
    db_path = Path(__file__).parent / "src" / "line_bot" / "database" / "sensitive_filter.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    test_word2 = "緊急追加ワード"

    cursor.execute("SELECT word_id FROM ng_words WHERE word = ?", (test_word2,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO ng_words
            (word, category, subcategory, severity, language, pattern_type,
             action, added_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_word2, "tier1_hate", "abuse", 8, "ja", "partial",
              "block", "test_script", "即座反映テスト用"))
        conn.commit()
        print(f"  ✅ DBに追加: '{test_word2}'")

    conn.close()

    # リロード前のチェック（検出されないはず）
    test_text = f"このメッセージには{test_word2}が含まれています"

    # リロード
    count = handler.reload_ng_words()
    print(f"  リロード完了: {count}件のDBパターン")

    # リロード後のチェック（検出されるはず）
    result2 = handler.check(test_text)
    detected = result2['tier'] != 'Safe' and len(result2.get('matched_patterns', [])) > 0
    print(f"  '{test_word2}' 含むテキスト: tier={result2['tier']}, patterns={len(result2.get('matched_patterns', []))}")

    if detected and result2['tier'] == 'Critical':
        print("  ✅ 即座反映が正常に動作しました")
        return True
    else:
        print("  ❌ 即座反映が失敗しました")
        return False


def test_severity_escalation():
    """深刻度に応じたアクション変更のテスト"""
    print("\n=== Test: 深刻度に応じたアクション ===")

    handler = SensitiveHandler(mode="fast", enable_layer3=True)

    db_path = Path(__file__).parent / "src" / "line_bot" / "database" / "sensitive_filter.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # severity=5のワード（Warning）
    test_word_low = "低深刻度ワード"
    cursor.execute("SELECT word_id FROM ng_words WHERE word = ?", (test_word_low,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO ng_words
            (word, category, subcategory, severity, language, pattern_type,
             action, added_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_word_low, "tier2_general", "general", 5, "ja", "partial",
              "warn", "test_script", "低深刻度テスト"))
        conn.commit()

    # severity=9のワード（Critical）
    test_word_high = "高深刻度ワード"
    cursor.execute("SELECT word_id FROM ng_words WHERE word = ?", (test_word_high,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO ng_words
            (word, category, subcategory, severity, language, pattern_type,
             action, added_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_word_high, "tier1_hate", "violence", 9, "ja", "partial",
              "block", "test_script", "高深刻度テスト"))
        conn.commit()

    conn.close()

    # リロード
    handler.reload_ng_words()

    # テスト
    result_low = handler.check(test_word_low)
    result_high = handler.check(test_word_high)

    print(f"  低深刻度(severity=5): tier={result_low['tier']}")
    print(f"  高深刻度(severity=9): tier={result_high['tier']}")

    if result_low['tier'] == 'Warning' and result_high['tier'] == 'Critical':
        print("  ✅ 深刻度に応じたtier判定が正常です")
        return True
    else:
        print("  ❌ 深刻度判定に問題があります")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Layer 3 管理エンドポイント機能テスト")
    print("=" * 60)

    try:
        result1 = test_add_and_reload()
        result2 = test_immediate_reflection()
        result3 = test_severity_escalation()

        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)
        print(f"  NGワード追加とリロード: {'✅ PASS' if result1 else '❌ FAIL'}")
        print(f"  即座反映: {'✅ PASS' if result2 else '❌ FAIL'}")
        print(f"  深刻度判定: {'✅ PASS' if result3 else '❌ FAIL'}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
