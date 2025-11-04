#!/usr/bin/env python3
"""
Copy Robot Database Viewer (Simple Plain Text)
シンプルなプレーンテキスト版 - リソース最小化

Author: Claude Code
Date: 2025-10-24
"""

from flask import Flask, request
import sqlite3

app = Flask(__name__)
COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"


def get_db():
    conn = sqlite3.connect(COPY_ROBOT_DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    """ホーム - 統計表示"""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM sister_shared_events")
    events = c.fetchone()[0]

    # キャラクター別テーブルの合計
    c.execute("""
        SELECT
            (SELECT COUNT(*) FROM botan_memories) +
            (SELECT COUNT(*) FROM kasho_memories) +
            (SELECT COUNT(*) FROM yuri_memories)
    """)
    memories = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM inspiration_events")
    inspirations = c.fetchone()[0]

    c.execute("SELECT MAX(event_id) FROM sister_shared_events")
    latest = c.fetchone()[0]

    conn.close()

    return f"""Copy Robot Database Viewer
========================================

Database: sisters_memory_COPY_ROBOT_20251024_143000.db
Test Environment Only (本物の魂ではありません)

Statistics:
  Total Events: {events}
  Total Memories: {memories}
  Total Inspirations: {inspirations}
  Latest Event ID: {latest}

Pages:
  /events - イベント一覧
  /memories - 個別記憶一覧
  /inspirations - Inspiration一覧
  /event/<id> - イベント詳細
  /inspiration/<id> - Inspiration詳細

========================================
"""


@app.route('/events')
def events():
    """イベント一覧"""
    conn = get_db()
    c = conn.cursor()

    search = request.args.get('search', '')
    if search:
        c.execute("""
            SELECT event_id, event_name, event_date, location, created_at
            FROM sister_shared_events
            WHERE event_name LIKE ? OR description LIKE ?
            ORDER BY event_id DESC
        """, (f'%{search}%', f'%{search}%'))
    else:
        c.execute("""
            SELECT event_id, event_name, event_date, location, created_at
            FROM sister_shared_events
            ORDER BY event_id DESC
        """)

    events = c.fetchall()
    conn.close()

    output = "Events List\n" + "="*80 + "\n\n"
    output += f"Total: {len(events)} events\n"
    if search:
        output += f"Search: '{search}'\n"
    output += f"URL: /events?search=キーワード でイベント検索可能\n\n"
    output += "-"*80 + "\n"

    for e in events:
        output += f"Event #{e['event_id']}: {e['event_name']}\n"
        output += f"  Date: {e['event_date'] or 'N/A'}\n"
        output += f"  Location: {e['location'] or 'N/A'}\n"
        output += f"  Created: {e['created_at']}\n"
        output += f"  Detail: /event/{e['event_id']}\n"
        output += "-"*80 + "\n"

    return f"<pre>{output}</pre>"


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    """イベント詳細"""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM sister_shared_events WHERE event_id = ?", (event_id,))
    e = c.fetchone()

    if not e:
        conn.close()
        return f"<pre>Event #{event_id} not found</pre>", 404

    # キャラクター別テーブルから記憶を取得
    c.execute(f"""
        SELECT 'botan' as character, diary_entry, created_at
        FROM botan_memories WHERE event_id = ?
        UNION ALL
        SELECT 'kasho' as character, diary_entry, created_at
        FROM kasho_memories WHERE event_id = ?
        UNION ALL
        SELECT 'yuri' as character, diary_entry, created_at
        FROM yuri_memories WHERE event_id = ?
    """, (event_id, event_id, event_id))
    memories = c.fetchall()

    conn.close()

    output = f"Event #{e['event_id']} Details\n" + "="*80 + "\n\n"
    output += f"Event Name: {e['event_name']}\n"
    output += f"Date: {e['event_date'] or 'N/A'}\n"
    output += f"Location: {e['location'] or 'N/A'}\n"
    output += f"Category: {e['category'] or 'N/A'}\n"
    output += f"Created: {e['created_at']}\n\n"

    if e['description']:
        output += "Description:\n" + "-"*80 + "\n"
        output += e['description'] + "\n"
        output += "-"*80 + "\n\n"

    output += f"Individual Memories ({len(memories)}):\n" + "-"*80 + "\n"
    for m in memories:
        output += f"[{m[0]}] {m[2]}\n"  # character, created_at
        output += f"{m[1]}\n"  # memory_text
        output += "-"*80 + "\n"

    output += "\nBack to /events\n"

    return f"<pre>{output}</pre>"


@app.route('/memories')
def memories():
    """個別記憶一覧"""
    conn = get_db()
    c = conn.cursor()

    char = request.args.get('character', '')

    if char == 'botan':
        c.execute("""
            SELECT memory_id, 'botan' as character, event_id, diary_entry, created_at
            FROM botan_memories
            ORDER BY memory_id DESC
            LIMIT 50
        """)
    elif char == 'kasho':
        c.execute("""
            SELECT memory_id, 'kasho' as character, event_id, diary_entry, created_at
            FROM kasho_memories
            ORDER BY memory_id DESC
            LIMIT 50
        """)
    elif char == 'yuri':
        c.execute("""
            SELECT memory_id, 'yuri' as character, event_id, diary_entry, created_at
            FROM yuri_memories
            ORDER BY memory_id DESC
            LIMIT 50
        """)
    else:
        # 全キャラクター
        c.execute("""
            SELECT memory_id, 'botan' as character, event_id, diary_entry, created_at
            FROM botan_memories
            UNION ALL
            SELECT memory_id, 'kasho' as character, event_id, diary_entry, created_at
            FROM kasho_memories
            UNION ALL
            SELECT memory_id, 'yuri' as character, event_id, diary_entry, created_at
            FROM yuri_memories
            ORDER BY 1 DESC
            LIMIT 50
        """)

    mems = c.fetchall()
    conn.close()

    output = "Individual Memories\n" + "="*80 + "\n\n"
    output += f"Total: {len(mems)} (最新50件)\n"
    if char:
        output += f"Character Filter: {char}\n"
    output += f"URL: /memories?character=botan|kasho|yuri でフィルタ可能\n\n"
    output += "-"*80 + "\n"

    for m in mems:
        output += f"Memory #{m[0]} [{m[1]}] Event #{m[2]}\n"  # memory_id, character, event_id
        output += f"  Text: {m[3][:100]}{'...' if len(m[3]) > 100 else ''}\n"  # memory_text
        output += f"  Created: {m[4]}\n"  # created_at
        output += "-"*80 + "\n"

    return f"<pre>{output}</pre>"


@app.route('/inspirations')
def inspirations():
    """Inspiration一覧"""
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("""
            SELECT inspiration_id, character, original_hallucination, inspired_value,
                   status, confidence, mention_count, event_id_origin, created_at
            FROM inspiration_events
            ORDER BY inspiration_id DESC
        """)
        insps = c.fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return "<pre>Inspiration table not found (ハルシネーションシステム未実行)</pre>"

    conn.close()

    output = "Inspirations - 嘘から出た実\n" + "="*80 + "\n\n"
    output += f"Total: {len(insps)}\n"
    output += f"Status: seed -> growing -> realized\n\n"
    output += "-"*80 + "\n"

    for i in insps:
        output += f"Inspiration #{i['inspiration_id']} [{i['character']}] Status: {i['status']}\n"
        output += f"  Inspired Value: {i['inspired_value']}\n"
        output += f"  Confidence: {i['confidence']:.2f}, Mentions: {i['mention_count']}\n"
        output += f"  Origin Event: #{i['event_id_origin']}\n"
        output += f"  Original: {i['original_hallucination']}\n"
        output += f"  Created: {i['created_at']}\n"
        output += f"  Detail: /inspiration/{i['inspiration_id']}\n"
        output += "-"*80 + "\n"

    return f"<pre>{output}</pre>"


@app.route('/inspiration/<int:inspiration_id>')
def inspiration_detail(inspiration_id):
    """Inspiration詳細"""
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM inspiration_events WHERE inspiration_id = ?", (inspiration_id,))
        i = c.fetchone()
    except sqlite3.OperationalError:
        conn.close()
        return "<pre>Inspiration table not found</pre>", 404

    if not i:
        conn.close()
        return f"<pre>Inspiration #{inspiration_id} not found</pre>", 404

    conn.close()

    output = f"Inspiration #{i['inspiration_id']} Details\n" + "="*80 + "\n\n"
    output += f"Character: {i['character']}\n"
    output += f"Status: {i['status']}\n"
    output += f"Confidence: {i['confidence']:.2f}\n"
    output += f"Mention Count: {i['mention_count']}\n\n"

    output += "Original Hallucination:\n" + "-"*80 + "\n"
    output += i['original_hallucination'] + "\n"
    output += "-"*80 + "\n\n"

    output += "Inspired Value:\n" + "-"*80 + "\n"
    output += i['inspired_value'] + "\n"
    output += "-"*80 + "\n\n"

    output += "Timeline:\n"
    output += f"  Origin Event ID: {i['event_id_origin']}\n"
    output += f"  Created: {i['created_at']}\n"
    output += f"  Last Mentioned: {i['last_mentioned_at']}\n"
    if i['realized_at']:
        output += f"  Realized: {i['realized_at']}\n"
        output += f"  Realization Event: {i['event_id_realization']}\n"

    output += "\nBack to /inspirations\n"

    return f"<pre>{output}</pre>"


if __name__ == '__main__':
    print("Copy Robot Database Viewer (Simple)")
    print("Access: http://localhost:5000")
    print("Database: " + COPY_ROBOT_DB)
    print()
    app.run(host='0.0.0.0', port=5000, debug=False)
