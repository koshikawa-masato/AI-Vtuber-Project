#!/usr/bin/env python3
"""View all 98 memories of Botan"""
import sqlite3

db_path = "sisters_memory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT bm.event_id, sse.botan_absolute_day, sse.event_name, 
           bm.botan_emotion, bm.botan_thought, bm.diary_entry
    FROM botan_memories bm
    JOIN sister_shared_events sse ON bm.event_id = sse.event_id
    ORDER BY sse.botan_absolute_day
""")

print("="*80)
print("牡丹の全記憶（98件）")
print("="*80)
print()

for idx, row in enumerate(cursor.fetchall(), 1):
    event_id, abs_day, event_name, emotion, thought, diary = row
    age_years = abs_day // 365
    age_months = (abs_day % 365) // 30
    
    print(f"【記憶 {idx}/98】Event #{event_id:03d} - {age_years}歳{age_months}ヶ月")
    print(f"出来事: {event_name}")
    print(f"感情: {emotion}")
    if thought:
        print(f"思考: {thought[:100]}..." if len(thought) > 100 else f"思考: {thought}")
    if diary:
        print(f"日記: {diary[:100]}..." if len(diary) > 100 else f"日記: {diary}")
    print()

conn.close()
