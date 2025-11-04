#!/usr/bin/env python3
"""
Copy Robot Discussion Test
コピーロボットで実際の討論を1回実行してInspiration記録をテスト

Author: Claude Code
Date: 2025-10-24
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Copy Robot DBパス
COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"
COPY_ROBOT_PROPOSALS = "/home/koshikawa/toExecUnit/proposals_COPY_ROBOT.json"

# Import memory generator components
from autonomous_discussion_v4_improved import StructuredDiscussionSystem
from hallucination_personalizer import HallucinationPersonalizer


async def test_single_discussion():
    """1つの討論を実行してInspirationをテスト"""

    print("=" * 80)
    print("Copy Robot Discussion Test - Single Proposal Execution")
    print("=" * 80)
    print()
    print(f"Database: {COPY_ROBOT_DB}")
    print(f"Test Proposal: #138 (Inspiration誘発議題)")
    print()

    # HallucinationPersonalizer初期化（コピーロボットDB指定）
    personalizer = HallucinationPersonalizer(
        memory_db_path=COPY_ROBOT_DB,
        enable_logging=True
    )

    # Discussion system初期化
    discussion_system = StructuredDiscussionSystem(
        hallucination_personalizer=personalizer
    )

    # Proposal #138を読み込み
    with open('/home/koshikawa/toExecUnit/proposals.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        proposals = data['proposals']

    # Proposal #138を探す
    proposal_138 = None
    for p in proposals:
        if p['id'] == 138:
            proposal_138 = p
            break

    if not proposal_138:
        print("❌ Proposal #138 not found")
        return

    print(f"Proposal #138: {proposal_138['title']}")
    print(f"Status: {proposal_138['status']}")
    print()
    print("Starting discussion...")
    print("-" * 80)

    # 討論実行
    discussion_proposal = {
        "title": proposal_138['title'],
        "description": proposal_138['description'],
        "priority": proposal_138['priority']
    }

    state = await discussion_system.run_structured_discussion(discussion_proposal)

    print("-" * 80)
    print("Discussion completed!")
    print()
    print(f"Total Rounds: {state.current_round}")
    print(f"Total Speeches: {len(state.transcript)}")
    print(f"Phase Transitions: {len(state.phase_history)}")
    print()

    # 討論記録を保存（コピーロボットDBに）
    discussion_system.save_discussion_record(state)
    print(f"✅ Discussion record saved")
    print()

    # Event #138として記憶を保存
    # （本来はMemoryGeneratorを使うが、ここでは簡易的にイベントだけ作成）
    conn = sqlite3.connect(COPY_ROBOT_DB)
    cursor = conn.cursor()

    # 次のevent_idを取得
    cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
    max_event = cursor.fetchone()[0]
    next_event_id = (max_event or 137) + 1

    print(f"Creating Event #{next_event_id}...")

    # イベント作成
    cursor.execute("""
        INSERT INTO sister_shared_events (
            event_id, event_name, event_date, location, category,
            description, participants, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        next_event_id,
        proposal_138['title'],
        datetime.now().strftime('%Y-%m-%d'),
        '牡丹の内部世界（討論システム）',
        '自律討論',
        f"テスト討論「{proposal_138['title']}」。Inspiration記録テスト。",
        'botan,kasho,yuri',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    print(f"✅ Event #{next_event_id} created")
    print()

    # Inspiration記録を確認
    cursor.execute("""
        SELECT inspiration_id, character, inspired_value,
               event_id_origin, status, confidence, mention_count
        FROM inspiration_events
        ORDER BY inspiration_id DESC
        LIMIT 5
    """)

    inspirations = cursor.fetchall()

    print("=" * 80)
    print("Inspiration Records (最新5件)")
    print("=" * 80)

    if inspirations:
        for insp in inspirations:
            print(f"Inspiration #{insp[0]}")
            print(f"  Character: {insp[1]}")
            print(f"  Inspired Value: {insp[2][:50]}...")
            print(f"  Origin Event: #{insp[3]}")
            print(f"  Status: {insp[4]}, Confidence: {insp[5]:.2f}, Mentions: {insp[6]}")
            print()
    else:
        print("No inspirations found")

    conn.close()

    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print()
    print("WebUIで確認:")
    print(f"  http://localhost:5000/inspirations")
    print(f"  http://localhost:5000/event/{next_event_id}")
    print()


if __name__ == '__main__':
    print()
    asyncio.run(test_single_discussion())
