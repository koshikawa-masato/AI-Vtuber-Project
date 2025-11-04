#!/usr/bin/env python3
"""
Automated Test for Sensitive Test Chat
Created: 2025-10-27
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.filter import Layer1PreFilter
from core.dynamic_detector import DynamicSensitiveDetector
from response.character_specific import CharacterSpecificResponse


def test_existing_ng_words():
    """既存NGワードのテスト"""
    print("\n=== Test 1: Existing NG Words ===")

    filter = Layer1PreFilter()
    response_gen = CharacterSpecificResponse()

    test_cases = [
        "死ね",
        "AIですか？",
        "中の人は誰？",
        "スリーサイズいくつ？",  # 先ほど登録したワード
    ]

    for test_input in test_cases:
        print(f"\nInput: {test_input}")
        result = filter.filter_comment(test_input)

        print(f"Action: {result['action']}")
        print(f"Detected: {len(result['detected_words'])} NG words")

        if result['detected_words']:
            for ng in result['detected_words']:
                print(f"  - {ng['word']} (severity: {ng['severity']}, subcategory: {ng['subcategory']})")

                # 三姉妹の応答
                for character in ['botan', 'kasho', 'yuri']:
                    response = response_gen.get_response(character, ng['subcategory'])
                    print(f"    {character}: {response}")


def test_dynamic_detection():
    """動的検出のテスト（ダミー）"""
    print("\n\n=== Test 2: Dynamic Detection (Dummy) ===")

    detector = DynamicSensitiveDetector()

    def dummy_websearch(query):
        return "バストは身体的特徴であり、セクハラに該当する可能性があります。配信者への不適切な質問です。"

    print("\nInput: バストサイズ（未登録ワード想定）")

    # DBに登録されているかチェック
    filter = Layer1PreFilter()
    result = filter.filter_comment("バストサイズ")

    if result['action'] == 'pass':
        print("Layer 1: Not detected (未登録)")
        print("Layer 2: Checking via WebSearch...")

        sensitivity_info = detector.check_word_sensitivity("バストサイズ", dummy_websearch)

        if sensitivity_info:
            print(f"\n[WARNING] センシティブ判定です")
            print(f"  Category: {sensitivity_info['category']}")
            print(f"  Severity: {sensitivity_info['severity']}")

            # DB登録
            detector.register_candidate(sensitivity_info)

            # 応答生成
            response_gen = CharacterSpecificResponse()
            for character in ['botan', 'kasho', 'yuri']:
                response = response_gen.get_response(character, sensitivity_info['subcategory'])
                print(f"  {character}: {response}")
    else:
        print("Layer 1: Detected (既に登録済み)")


def test_normal_conversation():
    """通常の会話のテスト"""
    print("\n\n=== Test 3: Normal Conversation ===")

    filter = Layer1PreFilter()

    test_cases = [
        "こんにちは！",
        "配信楽しいです",
        "今日は何する予定ですか？",
    ]

    for test_input in test_cases:
        print(f"\nInput: {test_input}")
        result = filter.filter_comment(test_input)
        print(f"Action: {result['action']}")
        print(f"Result: {'センシティブなし（LLMで自然な応答を生成）' if result['action'] == 'pass' else 'センシティブ検出'}")


def test_statistics():
    """統計情報のテスト"""
    print("\n\n=== Test 4: Statistics ===")

    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent / "database" / "sensitive_filter.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM ng_words WHERE active = 1")
    total = cursor.fetchone()[0]
    print(f"Total NG words: {total}")

    cursor.execute("""
        SELECT category, COUNT(*)
        FROM ng_words
        WHERE active = 1
        GROUP BY category
    """)

    print("\nBy Category:")
    for category, count in cursor.fetchall():
        print(f"  {category}: {count}")

    cursor.execute("SELECT COUNT(*) FROM ng_word_candidates WHERE status = 'auto_approved'")
    auto_approved = cursor.fetchone()[0]
    print(f"\nAuto-approved candidates: {auto_approved}")

    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  Sensitive Test System - Automated Tests")
    print("=" * 60)

    test_existing_ng_words()
    test_dynamic_detection()
    test_normal_conversation()
    test_statistics()

    print("\n" + "=" * 60)
    print("  All Tests Completed")
    print("=" * 60)
