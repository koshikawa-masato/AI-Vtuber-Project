#!/usr/bin/env python3
"""
Fix incorrect pronouns in Botan's memories
Replace "俺" with "私" or "うち"
"""

import sqlite3
import re

def fix_pronouns(db_path="sisters_memory.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all memories with "俺"
    cursor.execute("""
        SELECT memory_id, event_id, botan_thought, diary_entry
        FROM botan_memories
        WHERE botan_thought LIKE '%俺%' OR diary_entry LIKE '%俺%'
    """)
    
    memories_to_fix = cursor.fetchall()
    
    if not memories_to_fix:
        print("✅ 修正不要：記憶に「俺」は含まれていません")
        conn.close()
        return
    
    print(f"修正対象: {len(memories_to_fix)}件の記憶\n")
    
    fixed_count = 0
    for memory_id, event_id, thought, diary in memories_to_fix:
        print(f"Event #{event_id}:")
        
        # Fix thought
        new_thought = thought
        if thought and '俺' in thought:
            # Replace 俺 with 私
            new_thought = thought.replace('俺', '私')
            print(f"  思考（修正前）: {thought[:80]}...")
            print(f"  思考（修正後）: {new_thought[:80]}...")
        
        # Fix diary
        new_diary = diary
        if diary and '俺' in diary:
            # For diary, use more casual "あたし" or "私"
            new_diary = diary.replace('俺', '私')
            print(f"  日記（修正前）: {diary[:80]}...")
            print(f"  日記（修正後）: {new_diary[:80]}...")
        
        # Update database
        cursor.execute("""
            UPDATE botan_memories
            SET botan_thought = ?, diary_entry = ?
            WHERE memory_id = ?
        """, (new_thought, new_diary, memory_id))
        
        fixed_count += 1
        print(f"  ✅ 修正完了\n")
    
    conn.commit()
    conn.close()
    
    print(f"修正完了: {fixed_count}件の記憶を修正しました")

if __name__ == "__main__":
    print("="*60)
    print("牡丹の記憶の一人称修正スクリプト")
    print("="*60)
    print()
    
    response = input("記憶データベースの「俺」を「私」に修正しますか？ (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        fix_pronouns()
    else:
        print("キャンセルしました")
