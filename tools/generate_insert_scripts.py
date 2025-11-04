#!/usr/bin/env python3
"""
Phase D: Generate INSERT Scripts from Event Master Files
Parses Phase_D_カテゴリ*.md files and generates SQL INSERT statements
"""

import re
import sqlite3
from pathlib import Path
from datetime import datetime

def parse_event_file(file_path):
    """Parse a category markdown file and extract event data"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    events = []

    # Split by event sections (【イベントXXX】)
    event_sections = re.split(r'###\s+【イベント(\d+)】:', content)

    # event_sections[0] is header, then alternating event_id and event_content
    for i in range(1, len(event_sections), 2):
        if i + 1 >= len(event_sections):
            break

        event_id = int(event_sections[i].strip())
        event_content = event_sections[i + 1]

        event_data = parse_event_content(event_id, event_content)
        if event_data:
            events.append(event_data)

    return events

def parse_event_content(event_id, content):
    """Parse individual event content and extract fields"""

    event_data = {'event_number': event_id}

    # Extract event_name
    match = re.search(r'-\s+\*\*イベント名\*\*:\s*(.+)', content)
    if match:
        event_data['event_name'] = match.group(1).strip()

    # Extract event_date (実カレンダー)
    match = re.search(r'-\s+\*\*実カレンダー\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
    if match:
        event_data['event_date'] = match.group(1).strip()

    # Extract location
    match = re.search(r'-\s+\*\*場所\*\*:\s*(.+)', content)
    if match:
        location_raw = match.group(1).strip()
        # Normalize location
        if 'LA' in location_raw or 'ロサンゼルス' in location_raw:
            event_data['location'] = 'los_angeles'
        elif '日本' in location_raw:
            event_data['location'] = 'japan'
        else:
            event_data['location'] = 'other'

    # Extract emotional_impact
    match = re.search(r'-\s+\*\*感情的インパクト\*\*:\s*(\d+)', content)
    if match:
        event_data['emotional_impact'] = int(match.group(1).strip())

    # Extract ages and absolute days
    # Kasho
    match = re.search(r'Kasho:\s*(\d+)歳(\d+)日目\s*=\s*(\d+)日目', content)
    if match:
        event_data['kasho_age_years'] = int(match.group(1))
        event_data['kasho_age_days'] = int(match.group(2))
        event_data['kasho_absolute_day'] = int(match.group(3))

    # Botan
    match = re.search(r'牡丹:\s*(\d+)歳(\d+)日目\s*=\s*(\d+)日目', content)
    if match:
        event_data['botan_age_years'] = int(match.group(1))
        event_data['botan_age_days'] = int(match.group(2))
        event_data['botan_absolute_day'] = int(match.group(3))

    # Yuri
    match = re.search(r'ユリ:\s*(\d+)歳(\d+)日目\s*=\s*(\d+)日目', content)
    if match:
        event_data['yuri_age_years'] = int(match.group(1))
        event_data['yuri_age_days'] = int(match.group(2))
        event_data['yuri_absolute_day'] = int(match.group(3))

    # Extract description (何が起こったか)
    match = re.search(r'\*\*何が起こったか:\*\*\s*\n(.+?)(?:\n\n|\*\*参加者)', content, re.DOTALL)
    if match:
        event_data['description'] = match.group(1).strip()

    # Extract participants
    match = re.search(r'\*\*参加者:\*\*\s*\n(.+?)(?:\n\n|\*\*文化的背景)', content, re.DOTALL)
    if match:
        participants_raw = match.group(1).strip()
        # Extract bullet list items
        participants = re.findall(r'-\s+(.+)', participants_raw)
        event_data['participants'] = str(participants) if participants else None

    # Extract cultural_context
    match = re.search(r'\*\*文化的背景:\*\*\s*\n(.+?)(?:\n\n|####)', content, re.DOTALL)
    if match:
        event_data['cultural_context'] = match.group(1).strip()

    # Determine category based on event_number
    if 1 <= event_id <= 10:
        event_data['category'] = 'life_turning_point'
    elif 11 <= event_id <= 30:
        event_data['category'] = 'sisterhood'
    elif 31 <= event_id <= 45:
        event_data['category'] = 'encounter'
    elif 46 <= event_id <= 60:
        event_data['category'] = 'difficulty'
    elif 61 <= event_id <= 75:
        event_data['category'] = 'moving'
    elif 76 <= event_id <= 90:
        event_data['category'] = 'growth'
    elif 91 <= event_id <= 100:
        event_data['category'] = 'cultural'

    return event_data

def generate_insert_statement(event_data):
    """Generate SQL INSERT statement from event data"""

    fields = [
        'event_name', 'event_date', 'location',
        'kasho_age_years', 'kasho_age_days', 'kasho_absolute_day',
        'botan_age_years', 'botan_age_days', 'botan_absolute_day',
        'yuri_age_years', 'yuri_age_days', 'yuri_absolute_day',
        'description', 'participants', 'cultural_context',
        'emotional_impact', 'category', 'event_number'
    ]

    values = []
    for field in fields:
        value = event_data.get(field)
        if value is None:
            values.append('NULL')
        elif isinstance(value, int):
            values.append(str(value))
        else:
            # Escape single quotes
            value_escaped = str(value).replace("'", "''")
            values.append(f"'{value_escaped}'")

    sql = f"INSERT INTO sister_shared_events ({', '.join(fields)}) VALUES ({', '.join(values)});"

    return sql

def main():
    """Main function"""

    category_files = [
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ1_人生の転換点.md',
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ2_姉妹の絆.md',
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ3_重要な出会い.md',
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ4_困難・挫折.md',
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ5_感動的な出来事.md',
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ6_成長の瞬間.md',
        '/home/koshikawa/toExecUnit/Phase_D_カテゴリ7_文化的影響.md',
    ]

    all_events = []

    print("[INFO] Parsing event files...")

    for file_path in category_files:
        if not Path(file_path).exists():
            print(f"[WARNING] File not found: {file_path}")
            continue

        print(f"[INFO] Parsing: {Path(file_path).name}")
        events = parse_event_file(file_path)
        all_events.extend(events)
        print(f"[INFO] Found {len(events)} events")

    print(f"\n[INFO] Total events extracted: {len(all_events)}")

    # Generate SQL file
    output_path = '/home/koshikawa/toExecUnit/Phase_D_100件イベント_INSERT.sql'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("-- Phase D: 100件主要イベント INSERT文\n")
        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total Events: {len(all_events)}\n\n")

        for event in sorted(all_events, key=lambda x: x['event_number']):
            sql = generate_insert_statement(event)
            f.write(f"{sql}\n")

    print(f"\n[SUCCESS] INSERT script generated: {output_path}")
    print(f"[INFO] {len(all_events)} INSERT statements created")

    # Execute INSERTs
    print(f"\n[INFO] Executing INSERTs into database...")

    db_path = '/home/koshikawa/toExecUnit/sisters_memory.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for event in sorted(all_events, key=lambda x: x['event_number']):
        sql = generate_insert_statement(event)
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"[ERROR] Failed to insert Event {event['event_number']}: {e}")
            print(f"[DEBUG] SQL: {sql[:200]}...")

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM sister_shared_events")
    count = cursor.fetchone()[0]

    print(f"[SUCCESS] {count} events inserted into database")

    conn.close()

    return True

if __name__ == "__main__":
    main()
