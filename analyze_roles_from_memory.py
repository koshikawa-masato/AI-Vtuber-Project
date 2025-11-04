#!/usr/bin/env python3
"""
記憶DBから各姉妹の会話役割を分析するスクリプト
"""

import sqlite3
from collections import Counter

def analyze_role_from_memories(character: str) -> dict:
    """記憶から会話役割を抽出"""

    db_path = "/home/koshikawa/toExecUnit/sisters_memory.db"

    # Character to table mapping
    table_map = {
        "botan": "botan_memories",
        "kasho": "kasho_memories",
        "yuri": "yuri_memories"
    }

    table = table_map.get(character.lower())
    if not table:
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Load all memories
        cursor.execute(f"""
            SELECT
                event_id,
                botan_action as own_action,
                botan_thought as own_thought,
                botan_emotion as own_emotion,
                diary_entry
            FROM {table}
        """ if character == "botan" else f"""
            SELECT
                event_id,
                kasho_action as own_action,
                kasho_thought as own_thought,
                kasho_emotion as own_emotion,
                diary_entry
            FROM {table}
        """ if character == "kasho" else f"""
            SELECT
                event_id,
                yuri_action as own_action,
                yuri_thought as own_thought,
                yuri_emotion as own_emotion,
                diary_entry
            FROM {table}
        """)
        memories = cursor.fetchall()

        # Analyze patterns
        role_indicators = {
            "提案役": [],  # 提案・発起人
            "評価役": [],  # 判断・評価
            "調整役": [],  # バランス・補足
            "サポート役": [],  # 支援・協力
        }

        for memory in memories:
            # Combine all text fields
            text = " ".join([
                memory['own_action'] or "",
                memory['own_thought'] or "",
                memory['own_emotion'] or "",
                memory['diary_entry'] or ""
            ]).lower()

            # 提案役の特徴
            if any(word in text for word in ['提案', '思いつ', 'アイデア', '始め', 'やろう', '企画', '発起', '新し']):
                role_indicators["提案役"].append(text[:100])

            # 評価役の特徴
            if any(word in text for word in ['判断', '評価', '考え', '分析', '検討', '慎重', '責任']):
                role_indicators["評価役"].append(text[:100])

            # 調整役の特徴
            if any(word in text for word in ['調和', 'バランス', '調整', '仲介', '折衷', '妥協', '協調']):
                role_indicators["調整役"].append(text[:100])

            # サポート役の特徴
            if any(word in text for word in ['支え', '協力', '手伝', 'サポート', '助け', '寄り添']):
                role_indicators["サポート役"].append(text[:100])

        # 最も多い役割を決定
        role_counts = {role: len(items) for role, items in role_indicators.items()}
        primary_role = max(role_counts, key=role_counts.get)

        result = {
            "character": character,
            "primary_role": primary_role,
            "role_counts": role_counts,
            "total_memories": len(memories),
            "examples": role_indicators[primary_role][:3]  # 上位3例
        }

        return result

    finally:
        conn.close()

# 各姉妹の役割を分析
for character in ["botan", "kasho", "yuri"]:
    print(f"\n{'='*70}")
    print(f"{character.upper()}の役割分析")
    print('='*70)

    result = analyze_role_from_memories(character)

    if result:
        print(f"主要役割: {result['primary_role']}")
        print(f"総記憶数: {result['total_memories']}")
        print(f"\n役割カウント:")
        for role, count in result['role_counts'].items():
            print(f"  {role}: {count}")
        print(f"\n例（{result['primary_role']}）:")
        for i, example in enumerate(result['examples'], 1):
            print(f"  {i}. {example[:100]}...")
    else:
        print("記憶が見つかりませんでした")
