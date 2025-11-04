#!/usr/bin/env python3
"""
Fix all detected issues in Botan's memories
"""

import sqlite3
import re


def fix_pronouns(conn):
    """Fix incorrect pronouns (俺 → 私, ぼく → 私)"""
    cursor = conn.cursor()
    
    print("\n【修正1】一人称の修正")
    print("="*60)
    
    # Get all memories with incorrect pronouns
    cursor.execute("""
        SELECT memory_id, event_id, botan_thought, diary_entry
        FROM botan_memories
        WHERE botan_thought LIKE '%俺%' OR botan_thought LIKE '%ぼく%' OR botan_thought LIKE '%僕%'
           OR diary_entry LIKE '%俺%' OR diary_entry LIKE '%ぼく%' OR diary_entry LIKE '%僕%'
    """)
    
    memories = cursor.fetchall()
    
    if not memories:
        print("✅ 修正不要\n")
        return 0
    
    print(f"修正対象: {len(memories)}件\n")
    
    fixed = 0
    for memory_id, event_id, thought, diary in memories:
        new_thought = thought
        new_diary = diary
        
        # Replace incorrect pronouns
        if thought:
            new_thought = thought.replace('俺', '私').replace('ぼく', '私').replace('僕', '私')
        
        if diary:
            new_diary = diary.replace('俺', '私').replace('ぼく', '私').replace('僕', '私')
        
        if new_thought != thought or new_diary != diary:
            cursor.execute("""
                UPDATE botan_memories
                SET botan_thought = ?, diary_entry = ?
                WHERE memory_id = ?
            """, (new_thought, new_diary, memory_id))
            
            print(f"Event #{event_id}: 修正完了")
            fixed += 1
    
    print(f"\n✅ {fixed}件を修正\n")
    return fixed


def fix_age_inappropriate(conn):
    """Fix age-inappropriate detailed thoughts/diaries for 0-2 year olds"""
    cursor = conn.cursor()
    
    print("\n【修正2】年齢不適切な記憶の修正")
    print("="*60)
    
    # Get 0-2 year old memories with detailed content
    cursor.execute("""
        SELECT bm.memory_id, bm.event_id, sse.botan_absolute_day,
               bm.botan_thought, bm.diary_entry
        FROM botan_memories bm
        JOIN sister_shared_events sse ON bm.event_id = sse.event_id
        WHERE sse.botan_absolute_day < 365 * 3
          AND (LENGTH(bm.botan_thought) > 10 OR LENGTH(bm.diary_entry) > 10)
    """)
    
    memories = cursor.fetchall()
    
    if not memories:
        print("✅ 修正不要\n")
        return 0
    
    print(f"修正対象: {len(memories)}件\n")
    
    fixed = 0
    for memory_id, event_id, abs_day, thought, diary in memories:
        age_years = abs_day // 365
        age_months = (abs_day % 365) // 30
        
        # For 0-2 year olds, clear thought and diary
        new_thought = ""
        new_diary = ""
        
        cursor.execute("""
            UPDATE botan_memories
            SET botan_thought = ?, diary_entry = ?
            WHERE memory_id = ?
        """, (new_thought, new_diary, memory_id))
        
        print(f"Event #{event_id} ({age_years}歳{age_months}ヶ月): 思考・日記をクリア")
        fixed += 1
    
    print(f"\n✅ {fixed}件を修正\n")
    return fixed


def backup_database(db_path):
    """Create backup of database"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ バックアップ作成: {backup_path}\n")
    return backup_path


def main():
    db_path = "sisters_memory.db"
    
    print("="*60)
    print("牡丹の記憶データベース 修正スクリプト")
    print("="*60)
    
    # Create backup
    print("\n【バックアップ作成】")
    backup_path = backup_database(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Fix issues
        fixed_pronouns = fix_pronouns(conn)
        fixed_age = fix_age_inappropriate(conn)
        
        # Commit changes
        conn.commit()
        
        # Summary
        print("="*60)
        print("修正完了サマリー")
        print("="*60)
        print(f"一人称修正: {fixed_pronouns}件")
        print(f"年齢不適切修正: {fixed_age}件")
        print(f"合計: {fixed_pronouns + fixed_age}件")
        print("="*60)
        
        print(f"\n✅ すべての修正が完了しました")
        print(f"バックアップ: {backup_path}")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        conn.rollback()
        print("変更はロールバックされました")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
