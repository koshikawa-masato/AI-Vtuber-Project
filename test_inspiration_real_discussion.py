#!/usr/bin/env python3
"""
Real Discussion Inspiration Test
実際の討論でInspiration記録をテスト（最小限の実装）

Author: Claude Code
Date: 2025-10-24
"""

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

# Copy Robot DB
COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"

# Import necessary components
from autonomous_discussion_v4_improved import StructuredDiscussionSystem
from hallucination_personalizer import HallucinationPersonalizer


async def run_inspiration_test():
    """Inspiration誘発討論を実行"""

    print("\n" + "=" * 80)
    print("Real Discussion Inspiration Test")
    print("=" * 80)
    print(f"\nDatabase: {COPY_ROBOT_DB}")
    print("Proposal: これから挑戦してみたいことは？ (Inspiration誘発)")
    print()

    # 1. Initialize hallucination personalizer with Copy Robot DB
    print("[1] Initializing Hallucination Personalizer...")
    personalizer = HallucinationPersonalizer(
        memory_db_path=COPY_ROBOT_DB,
        enable_logging=True
    )
    print("✅ Personalizer initialized (using Copy Robot DB)")
    print()

    # 2. Initialize discussion system
    print("[2] Initializing Discussion System...")
    discussion_system = StructuredDiscussionSystem(
        hallucination_personalizer=personalizer
    )
    print("✅ Discussion system initialized")
    print()

    # 3. Get next event ID
    print("[3] Getting next Event ID...")
    conn = sqlite3.connect(COPY_ROBOT_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
    max_event = cursor.fetchone()[0]
    next_event_id = (max_event or 137) + 1
    conn.close()

    print(f"✅ Next Event ID: #{next_event_id}")
    print()

    # 4. Create test proposal (Inspiration-inducing) with event_id
    print("[4] Creating test proposal...")
    proposal = {
        "title": "これから挑戦してみたいことは？",
        "description": """【開発者からのお願い】

将来挑戦してみたいことについて、自由に話し合ってください。

【話し合ってほしいこと】
1. いつかやってみたいことはありますか？
2. 次に挑戦してみたいことは何ですか？
3. 三姉妹で一緒にやってみたいことはありますか？
4. それを実現できたら、どんな気持ちになると思いますか？

【重要】
- 夢や希望について、自由に語ってください
- 「やってみたい！」という気持ちを大切に
- お互いの夢を応援し合ってください""",
        "priority": "developer",
        "event_id": next_event_id  # Link to event for Inspiration tracking
    }
    print(f"✅ Proposal: {proposal['title']}")
    print(f"   Event ID: #{next_event_id}")
    print()

    # 5. Run discussion
    print("[5] Running structured discussion...")
    print("-" * 80)

    state = await discussion_system.run_structured_discussion(proposal)

    print("-" * 80)
    print(f"✅ Discussion completed!")
    print(f"   Rounds: {state.current_round}")
    print(f"   Speeches: {len(state.all_speeches)}")
    print()

    # 6. Save discussion record
    print("[6] Saving discussion record...")
    discussion_system.save_discussion_record(state)
    print(f"✅ Record saved to discussion_technical_logs/")
    print()

    # 7. Create event in database
    print(f"[7] Creating Event #{next_event_id}...")
    conn = sqlite3.connect(COPY_ROBOT_DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sister_shared_events (
            event_id, event_name, event_date, location, category,
            description, participants, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        next_event_id,
        proposal['title'],
        datetime.now().strftime('%Y-%m-%d'),
        '牡丹の内部世界（討論システム）',
        '自律討論（テスト）',
        f"コピーロボットでInspiration記録テスト。議題: {proposal['title']}",
        'botan,kasho,yuri',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    print(f"✅ Event #{next_event_id} created")
    print()

    # 8. Check Inspiration records
    print("[8] Checking Inspiration records...")
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
        print("⚠️  No Inspirations found")
        print()
        print("Possible reasons:")
        print("  - No aspirational statements during discussion")
        print("  - Statements didn't trigger Inspiration classifier")
        print("  - HallucinationDetector didn't detect any hallucinations")
    else:
        print(f"✅ Found {len(inspirations)} Inspiration(s)")
        print()
        print("=" * 80)
        print("Inspiration Records")
        print("=" * 80)

        for insp in inspirations:
            insp_id, char, original, origin_event, value, status, conf, mentions, created = insp

            print(f"\nInspiration #{insp_id}")
            print(f"  Character: {char}")
            print(f"  Origin Event: #{origin_event}")
            if origin_event == 999:
                print(f"    ⚠️  This is test data (Event #999 doesn't exist)")
            elif origin_event == next_event_id:
                print(f"    ✅ THIS IS FROM TODAY'S DISCUSSION!")
            print(f"  Status: {status}")
            print(f"  Confidence: {conf:.2f}")
            print(f"  Mentions: {mentions}")
            print(f"  Created: {created}")
            print(f"  Original: {original[:80]}...")
            print(f"  Inspired Value: {value[:80]}...")

    conn.close()

    print()
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print()
    print("Check results in WebUI:")
    print(f"  Inspirations: http://localhost:5000/inspirations")
    print(f"  Event: http://localhost:5000/event/{next_event_id}")
    print()


if __name__ == '__main__':
    asyncio.run(run_inspiration_test())
