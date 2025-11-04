#!/usr/bin/env python3
"""
Finalize Inspiration Test - Post-processing Only
討論完了後の後処理（Event作成、Inspiration確認）

Author: Claude Code
Date: 2025-10-24
"""

import sqlite3
from datetime import datetime

COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"

def finalize_test():
    """後処理を実行"""

    print("=" * 80)
    print("Inspiration Test Finalization")
    print("=" * 80)
    print()

    conn = sqlite3.connect(COPY_ROBOT_DB)
    cursor = conn.cursor()

    # 1. Check current max event_id
    print("[1] Checking current Event ID...")
    cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
    max_event = cursor.fetchone()[0]
    next_event_id = (max_event or 137) + 1
    print(f"   Current max: Event #{max_event}")
    print(f"   Next ID: Event #{next_event_id}")
    print()

    # 2. Create Event #138
    print(f"[2] Creating Event #{next_event_id}...")

    proposal_title = "これから挑戦してみたいことは？"
    proposal_description = """【開発者からのお願い】

将来挑戦してみたいことについて、自由に話し合ってください。

【話し合ってほしいこと】
1. いつかやってみたいことはありますか？
2. 次に挑戦してみたいことは何ですか？
3. 三姉妹で一緒にやってみたいことはありますか？
4. それを実現できたら、どんな気持ちになると思いますか？

【重要】
- 夢や希望について、自由に語ってください
- 「やってみたい！」という気持ちを大切に
- お互いの夢を応援し合ってください"""

    cursor.execute("""
        INSERT INTO sister_shared_events (
            event_id, event_name, event_date, location, category,
            description, participants, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        next_event_id,
        proposal_title,
        datetime.now().strftime('%Y-%m-%d'),
        '牡丹の内部世界（討論システム）',
        '自律討論（テスト）',
        f"コピーロボットでInspiration記録テスト。議題: {proposal_title}\n\n結論: 三姉妹で料理教室を開く計画について討論（週2回、準備時間5時間以内、役割分担が必要）",
        'botan,kasho,yuri',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    print(f"   ✅ Event #{next_event_id} created")
    print()

    # 3. Check if Inspirations were recorded during discussion
    print("[3] Checking Inspiration records...")
    cursor.execute("""
        SELECT inspiration_id, character, original_hallucination,
               event_id_origin, inspired_value, status, confidence, mention_count,
               created_at
        FROM inspiration_events
        ORDER BY inspiration_id DESC
        LIMIT 10
    """)

    inspirations = cursor.fetchall()

    if not inspirations:
        print("   ⚠️  No Inspirations found in database")
        print()
        print("   Possible reasons:")
        print("   - HallucinationDetector didn't detect any hallucinations during discussion")
        print("   - Statements didn't trigger Inspiration classifier")
        print("   - System integration issue")
    else:
        print(f"   Found {len(inspirations)} Inspiration(s)")
        print()

        # Check if any are from today's discussion
        today_inspirations = [i for i in inspirations if i[3] == next_event_id]

        if today_inspirations:
            print(f"   ✅ {len(today_inspirations)} Inspiration(s) from Event #{next_event_id}!")
        else:
            print(f"   ℹ️  No Inspirations linked to Event #{next_event_id}")
            print(f"   Latest Inspirations are from other events:")
            for insp in inspirations[:3]:
                print(f"      - Inspiration #{insp[0]}: Event #{insp[3]} ({insp[1]})")

        print()
        print("   All Inspirations:")
        print("   " + "-" * 76)
        for insp in inspirations:
            insp_id, char, original, origin_event, value, status, conf, mentions, created = insp
            print(f"   Inspiration #{insp_id} [{char}] Origin: Event #{origin_event}")
            print(f"      Status: {status}, Confidence: {conf:.2f}, Mentions: {mentions}")
            print(f"      Inspired Value: {value[:60]}...")
            print(f"      Created: {created}")
            print()

    # 4. Check if discussion was recorded (technical log)
    print("[4] Discussion technical log status...")
    import os
    log_path = f"discussion_technical_logs/discussion_{next_event_id}_technical.md"

    if os.path.exists(log_path):
        print(f"   ✅ Technical log exists: {log_path}")
    else:
        print(f"   ⚠️  Technical log not found: {log_path}")
        print(f"   (Expected - discussion system crashed before saving)")

    print()

    # 5. Summary
    print("=" * 80)
    print("Test Finalization Complete")
    print("=" * 80)
    print()
    print(f"Event #{next_event_id}: {proposal_title}")
    print(f"Database: {COPY_ROBOT_DB}")
    print()
    print("Next steps:")
    print("  1. View in WebUI: http://localhost:5000/inspirations")
    print(f"  2. View Event: http://localhost:5000/event/{next_event_id}")
    print("  3. Check if HallucinationPersonalizer integration needs debugging")
    print()

    conn.close()


if __name__ == '__main__':
    finalize_test()
