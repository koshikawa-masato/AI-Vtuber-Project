#!/usr/bin/env python3
"""
Event ID Linking Verification Test
Quick test to verify event_id is properly linked in Inspiration records

Author: Claude Code
Date: 2025-10-24
"""

import asyncio
import sqlite3
from datetime import datetime

# Copy Robot DB
COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"

# Import necessary components
from autonomous_discussion_v4_improved import StructuredDiscussionSystem
from hallucination_personalizer import HallucinationPersonalizer


async def run_verification_test():
    """Quick verification test for event_id linking"""

    print("\n" + "=" * 80)
    print("Event ID Linking Verification Test")
    print("=" * 80)
    print()

    # 1. Get next event ID
    conn = sqlite3.connect(COPY_ROBOT_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
    max_event = cursor.fetchone()[0]
    next_event_id = (max_event or 137) + 1
    conn.close()

    print(f"[1] Next Event ID: #{next_event_id}")
    print()

    # 2. Initialize systems
    print("[2] Initializing systems...")
    personalizer = HallucinationPersonalizer(
        memory_db_path=COPY_ROBOT_DB,
        enable_logging=True
    )
    discussion_system = StructuredDiscussionSystem(
        hallucination_personalizer=personalizer
    )
    print("✅ Systems initialized")
    print()

    # 3. Create proposal with event_id
    print("[3] Creating test proposal...")
    proposal = {
        "title": "簡単な挑戦テスト",
        "description": "Event ID連携を検証するための簡単なテストです。",
        "priority": "test",
        "event_id": next_event_id  # THIS IS THE KEY FIX
    }
    print(f"✅ Proposal created with event_id: {next_event_id}")
    print()

    # 4. Run 2-round discussion (quick test)
    print("[4] Running quick discussion (2 rounds max)...")
    print("-" * 80)

    # Temporarily modify max rounds for quick test
    from autonomous_discussion_v4_improved import DiscussionPhase
    original_max_rounds = DiscussionPhase.MAX_ROUNDS.copy()
    DiscussionPhase.MAX_ROUNDS = {"起": 2, "承": 0, "転": 0, "結": 0}

    state = await discussion_system.run_structured_discussion(proposal, max_rounds=2)

    # Restore original max rounds
    DiscussionPhase.MAX_ROUNDS = original_max_rounds

    print("-" * 80)
    print(f"✅ Discussion completed!")
    print(f"   Rounds: {state.current_round}")
    print(f"   Speeches: {len(state.all_speeches)}")
    print()

    # 5. Create event in database
    print(f"[5] Creating Event #{next_event_id}...")
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
        'Event ID連携検証',
        f"Event ID連携バグ修正後の検証テスト。",
        'botan,kasho,yuri',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    print(f"✅ Event #{next_event_id} created")
    print()

    # 6. Check Inspirations with correct event_id
    print("[6] Checking Inspiration records...")
    cursor.execute("""
        SELECT inspiration_id, character, event_id_origin, status, confidence,
               created_at, original_hallucination
        FROM inspiration_events
        WHERE event_id_origin = ?
        ORDER BY inspiration_id DESC
    """, (next_event_id,))

    inspirations = cursor.fetchall()
    conn.close()

    if not inspirations:
        print("❌ FAILURE: No Inspirations with correct event_id found")
        print(f"   Expected event_id: {next_event_id}")
        print()
        print("Checking all Inspirations...")
        conn = sqlite3.connect(COPY_ROBOT_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT inspiration_id, character, event_id_origin
            FROM inspiration_events
            ORDER BY inspiration_id DESC
            LIMIT 5
        """)
        all_insp = cursor.fetchall()
        conn.close()
        for insp in all_insp:
            print(f"   Inspiration #{insp[0]}: {insp[1]}, event_id={insp[2]}")
        return False
    else:
        print(f"✅ SUCCESS: Found {len(inspirations)} Inspiration(s) with correct event_id!")
        print()
        print("=" * 80)
        print("Verification Result")
        print("=" * 80)

        for insp in inspirations:
            insp_id, char, origin_event, status, conf, created, original = insp

            print(f"\nInspiration #{insp_id}")
            print(f"  Character: {char}")
            print(f"  Origin Event: #{origin_event} ✅ CORRECT!")
            print(f"  Status: {status}")
            print(f"  Confidence: {conf:.2f}")
            print(f"  Created: {created}")
            print(f"  Original: {original[:60]}...")

        print()
        print("=" * 80)
        print("Event ID Linking: ✅ VERIFIED")
        print("=" * 80)
        return True


if __name__ == '__main__':
    success = asyncio.run(run_verification_test())
    exit(0 if success else 1)
