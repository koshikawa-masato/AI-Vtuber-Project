#!/usr/bin/env python3
"""
Copy Robot Database Viewer (Web UI)
コピーロボットのデータベース内容を参照するWebアプリケーション

開発者がテスト結果を確認するためのツール
本物の魂(sisters_memory.db)は表示しない（安全のため）

Author: Claude Code
Date: 2025-10-24
Version: 1.0
"""

from flask import Flask, render_template_string, request, jsonify
import sqlite3
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)

# コピーロボットDBのパス
COPY_ROBOT_DB = "/home/koshikawa/toExecUnit/sisters_memory_COPY_ROBOT_20251024_143000.db"

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>コピーロボット DB Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .warning {
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            margin: 20px;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
        }
        .nav {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }
        .nav a {
            flex: 1;
            padding: 15px;
            text-align: center;
            text-decoration: none;
            color: #495057;
            font-weight: 500;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        .nav a:hover {
            background: #e9ecef;
            color: #667eea;
        }
        .nav a.active {
            color: #667eea;
            border-bottom-color: #667eea;
            background: white;
        }
        .content {
            padding: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card h3 { font-size: 2em; margin-bottom: 5px; }
        .stat-card p { opacity: 0.9; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
        }
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }
        tr:hover { background: #f8f9fa; }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .badge-seed { background: #ffc107; color: #000; }
        .badge-growing { background: #17a2b8; color: white; }
        .badge-realized { background: #28a745; color: white; }
        .search-box {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .search-box input {
            width: 100%;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            font-size: 1em;
        }
        .detail-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .detail-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }
        .detail-row {
            display: grid;
            grid-template-columns: 200px 1fr;
            padding: 10px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .detail-row:last-child { border-bottom: none; }
        .detail-label {
            font-weight: 600;
            color: #495057;
        }
        .detail-value {
            color: #212529;
        }
        pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 コピーロボット Database Viewer</h1>
            <p>Copy Robot: sisters_memory_COPY_ROBOT_20251024_143000.db</p>
            <p style="font-size: 0.9em; margin-top: 10px;">
                📅 Created: 2025-10-24 14:30 | 📊 Size: 556KB | 🧪 Test Environment Only
            </p>
        </div>

        <div class="warning">
            ⚠️ <strong>テスト環境専用</strong>: このデータベースはコピーロボット（テスト用）です。本物の三姉妹の魂(sisters_memory.db)ではありません。
        </div>

        <div class="nav">
            <a href="/" class="{{ 'active' if page == 'home' else '' }}">🏠 ホーム</a>
            <a href="/events" class="{{ 'active' if page == 'events' else '' }}">📅 イベント一覧</a>
            <a href="/memories" class="{{ 'active' if page == 'memories' else '' }}">💭 個別記憶</a>
            <a href="/inspirations" class="{{ 'active' if page == 'inspirations' else '' }}">✨ Inspiration</a>
        </div>

        <div class="content">
            {% block content %}{% endblock %}
        </div>
    </div>
</body>
</html>
"""

HOME_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>📊 Database Statistics</h2>

<div class="stats">
    <div class="stat-card">
        <h3>{{ stats.total_events }}</h3>
        <p>総イベント数</p>
    </div>
    <div class="stat-card">
        <h3>{{ stats.total_memories }}</h3>
        <p>総記憶数</p>
    </div>
    <div class="stat-card">
        <h3>{{ stats.total_inspirations }}</h3>
        <p>Inspiration Seeds</p>
    </div>
    <div class="stat-card">
        <h3>{{ stats.latest_event }}</h3>
        <p>最新イベントID</p>
    </div>
</div>

<h2>🎯 主要機能</h2>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
    <div class="detail-card">
        <h3>📅 イベント一覧</h3>
        <p>三姉妹が経験した共有イベントを時系列で表示します。</p>
        <a href="/events" class="btn" style="margin-top: 10px;">イベント一覧へ →</a>
    </div>
    <div class="detail-card">
        <h3>💭 個別記憶</h3>
        <p>牡丹・Kasho・ユリそれぞれの個別記憶を参照できます。</p>
        <a href="/memories" class="btn" style="margin-top: 10px;">記憶一覧へ →</a>
    </div>
    <div class="detail-card">
        <h3>✨ Inspiration</h3>
        <p>「嘘から出た実」システムで記録されたInspiration seedsを確認できます。</p>
        <a href="/inspirations" class="btn" style="margin-top: 10px;">Inspirationへ →</a>
    </div>
</div>

<h2 style="margin-top: 30px;">📝 テスト情報</h2>
<div class="detail-card">
    <div class="detail-row">
        <div class="detail-label">データベース名</div>
        <div class="detail-value">sisters_memory_COPY_ROBOT_20251024_143000.db</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">作成日時</div>
        <div class="detail-value">2025-10-24 14:30:00</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">テスト内容</div>
        <div class="detail-value">Phase 3 Hallucination Personalization System (3-type classification + Inspiration tracking)</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">テスト結果</div>
        <div class="detail-value">✅ 成功 (5 test cases, 平均処理時間 0.83ms)</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">レポート</div>
        <div class="detail-value">HALLUCINATION_SYSTEM_TEST_REPORT_20251024.md</div>
    </div>
</div>
{% endblock %}
"""


def get_db_connection():
    """コピーロボットDBへの接続"""
    conn = sqlite3.connect(COPY_ROBOT_DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    """ホームページ"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 統計情報取得
    cursor.execute("SELECT COUNT(*) FROM sister_shared_events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sister_individual_memories")
    total_memories = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inspiration_events")
    total_inspirations = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(event_id) FROM sister_shared_events")
    latest_event = cursor.fetchone()[0]

    conn.close()

    stats = {
        'total_events': total_events,
        'total_memories': total_memories,
        'total_inspirations': total_inspirations,
        'latest_event': latest_event
    }

    return render_template_string(BASE_TEMPLATE + HOME_TEMPLATE, page='home', stats=stats)


@app.route('/events')
def events():
    """イベント一覧"""
    conn = get_db_connection()
    cursor = conn.cursor()

    search = request.args.get('search', '')

    if search:
        cursor.execute("""
            SELECT event_id, event_name, event_date, location, category, created_at
            FROM sister_shared_events
            WHERE event_name LIKE ? OR description LIKE ?
            ORDER BY event_id DESC
        """, (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("""
            SELECT event_id, event_name, event_date, location, category, created_at
            FROM sister_shared_events
            ORDER BY event_id DESC
        """)

    events = cursor.fetchall()
    conn.close()

    events_html = """
{% extends "base.html" %}
{% block content %}
<h2>📅 イベント一覧</h2>

<div class="search-box">
    <form method="get" action="/events">
        <input type="text" name="search" placeholder="イベント名や説明で検索..." value="{{ search }}">
    </form>
</div>

<p><strong>総イベント数:</strong> {{ events|length }}</p>

<table>
    <thead>
        <tr>
            <th>Event ID</th>
            <th>イベント名</th>
            <th>日付</th>
            <th>場所</th>
            <th>カテゴリ</th>
            <th>作成日時</th>
            <th>詳細</th>
        </tr>
    </thead>
    <tbody>
        {% for event in events %}
        <tr>
            <td><strong>#{{ event.event_id }}</strong></td>
            <td>{{ event.event_name }}</td>
            <td>{{ event.event_date or '-' }}</td>
            <td>{{ event.location or '-' }}</td>
            <td>{{ event.category or '-' }}</td>
            <td>{{ event.created_at }}</td>
            <td><a href="/event/{{ event.event_id }}" class="btn">詳細 →</a></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
"""

    return render_template_string(BASE_TEMPLATE + events_html, page='events', events=events, search=search)


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    """イベント詳細"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sister_shared_events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()

    if not event:
        conn.close()
        return "Event not found", 404

    # 関連する個別記憶を取得
    cursor.execute("""
        SELECT character, memory_text, memory_type, emotional_weight, created_at
        FROM sister_individual_memories
        WHERE event_id = ?
        ORDER BY character
    """, (event_id,))
    memories = cursor.fetchall()

    conn.close()

    detail_html = """
{% extends "base.html" %}
{% block content %}
<h2>📅 Event #{{ event.event_id }}: {{ event.event_name }}</h2>

<div class="detail-card">
    <h3>基本情報</h3>
    <div class="detail-row">
        <div class="detail-label">Event ID</div>
        <div class="detail-value">{{ event.event_id }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">イベント名</div>
        <div class="detail-value">{{ event.event_name }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">日付</div>
        <div class="detail-value">{{ event.event_date or '-' }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">場所</div>
        <div class="detail-value">{{ event.location or '-' }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">カテゴリ</div>
        <div class="detail-value">{{ event.category or '-' }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">作成日時</div>
        <div class="detail-value">{{ event.created_at }}</div>
    </div>
</div>

{% if event.description %}
<div class="detail-card">
    <h3>説明</h3>
    <pre>{{ event.description }}</pre>
</div>
{% endif %}

<div class="detail-card">
    <h3>💭 個別記憶 ({{ memories|length }}件)</h3>
    {% if memories %}
        <table>
            <thead>
                <tr>
                    <th>キャラクター</th>
                    <th>記憶タイプ</th>
                    <th>感情の重み</th>
                    <th>記憶内容</th>
                </tr>
            </thead>
            <tbody>
                {% for memory in memories %}
                <tr>
                    <td><strong>{{ memory.character }}</strong></td>
                    <td>{{ memory.memory_type }}</td>
                    <td>{{ memory.emotional_weight }}</td>
                    <td>{{ memory.memory_text[:100] }}{% if memory.memory_text|length > 100 %}...{% endif %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <p>個別記憶はありません。</p>
    {% endif %}
</div>

<a href="/events" class="btn">← イベント一覧に戻る</a>
{% endblock %}
"""

    return render_template_string(BASE_TEMPLATE + detail_html, page='events', event=event, memories=memories)


@app.route('/memories')
def memories():
    """個別記憶一覧"""
    conn = get_db_connection()
    cursor = conn.cursor()

    character = request.args.get('character', '')

    if character:
        cursor.execute("""
            SELECT memory_id, character, event_id, memory_text, memory_type, emotional_weight, created_at
            FROM sister_individual_memories
            WHERE character = ?
            ORDER BY memory_id DESC
            LIMIT 100
        """, (character,))
    else:
        cursor.execute("""
            SELECT memory_id, character, event_id, memory_text, memory_type, emotional_weight, created_at
            FROM sister_individual_memories
            ORDER BY memory_id DESC
            LIMIT 100
        """)

    memories = cursor.fetchall()
    conn.close()

    memories_html = """
{% extends "base.html" %}
{% block content %}
<h2>💭 個別記憶</h2>

<div class="search-box">
    <form method="get" action="/memories">
        <select name="character" onchange="this.form.submit()" style="padding: 10px; border: 1px solid #dee2e6; border-radius: 4px; font-size: 1em;">
            <option value="">全キャラクター</option>
            <option value="botan" {{ 'selected' if character == 'botan' else '' }}>牡丹 (botan)</option>
            <option value="kasho" {{ 'selected' if character == 'kasho' else '' }}>Kasho</option>
            <option value="yuri" {{ 'selected' if character == 'yuri' else '' }}>ユリ (yuri)</option>
        </select>
    </form>
</div>

<p><strong>表示件数:</strong> {{ memories|length }} (最新100件)</p>

<table>
    <thead>
        <tr>
            <th>Memory ID</th>
            <th>キャラクター</th>
            <th>Event ID</th>
            <th>タイプ</th>
            <th>感情の重み</th>
            <th>記憶内容（抜粋）</th>
            <th>作成日時</th>
        </tr>
    </thead>
    <tbody>
        {% for memory in memories %}
        <tr>
            <td><strong>#{{ memory.memory_id }}</strong></td>
            <td>{{ memory.character }}</td>
            <td><a href="/event/{{ memory.event_id }}" class="btn">Event #{{ memory.event_id }}</a></td>
            <td>{{ memory.memory_type }}</td>
            <td>{{ memory.emotional_weight }}</td>
            <td>{{ memory.memory_text[:80] }}{% if memory.memory_text|length > 80 %}...{% endif %}</td>
            <td>{{ memory.created_at }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
"""

    return render_template_string(BASE_TEMPLATE + memories_html, page='memories', memories=memories, character=character)


@app.route('/inspirations')
def inspirations():
    """Inspiration一覧"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT inspiration_id, character, original_hallucination, event_id_origin,
                   inspired_value, status, confidence, mention_count,
                   created_at, last_mentioned_at, realized_at
            FROM inspiration_events
            ORDER BY inspiration_id DESC
        """)
        inspirations = cursor.fetchall()
    except sqlite3.OperationalError:
        # テーブルが存在しない場合
        inspirations = []

    conn.close()

    inspirations_html = """
{% extends "base.html" %}
{% block content %}
<h2>✨ Inspiration Seeds - 「嘘から出た実」</h2>

<div class="detail-card">
    <p><strong>「嘘から出た実（まこと）」システム:</strong> 最初はハルシネーション（嘘・ごっこ遊び）でも、何度も語ることで本当の願いになる。そんな成長を記録するシステムです。</p>
    <p style="margin-top: 10px;"><strong>Status:</strong>
        <span class="badge badge-seed">seed</span> (初回言及) →
        <span class="badge badge-growing">growing</span> (繰り返し言及) →
        <span class="badge badge-realized">realized</span> (実現)
    </p>
</div>

<p><strong>総Inspiration数:</strong> {{ inspirations|length }}</p>

{% if inspirations %}
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>キャラクター</th>
            <th>Status</th>
            <th>Inspired Value</th>
            <th>Confidence</th>
            <th>Mention Count</th>
            <th>Origin Event</th>
            <th>Created</th>
            <th>詳細</th>
        </tr>
    </thead>
    <tbody>
        {% for insp in inspirations %}
        <tr>
            <td><strong>#{{ insp.inspiration_id }}</strong></td>
            <td>{{ insp.character }}</td>
            <td>
                <span class="badge badge-{{ insp.status }}">{{ insp.status }}</span>
            </td>
            <td>{{ insp.inspired_value[:50] }}{% if insp.inspired_value|length > 50 %}...{% endif %}</td>
            <td>{{ "%.2f"|format(insp.confidence) }}</td>
            <td>{{ insp.mention_count }}</td>
            <td><a href="/event/{{ insp.event_id_origin }}" class="btn">Event #{{ insp.event_id_origin }}</a></td>
            <td>{{ insp.created_at }}</td>
            <td><a href="/inspiration/{{ insp.inspiration_id }}" class="btn">詳細 →</a></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="warning">
    ℹ️ Inspirationデータがありません。ハルシネーションシステムがまだ実行されていない可能性があります。
</div>
{% endif %}
{% endblock %}
"""

    return render_template_string(BASE_TEMPLATE + inspirations_html, page='inspirations', inspirations=inspirations)


@app.route('/inspiration/<int:inspiration_id>')
def inspiration_detail(inspiration_id):
    """Inspiration詳細"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM inspiration_events WHERE inspiration_id = ?
        """, (inspiration_id,))
        insp = cursor.fetchone()
    except sqlite3.OperationalError:
        conn.close()
        return "Inspiration table not found", 404

    if not insp:
        conn.close()
        return "Inspiration not found", 404

    conn.close()

    detail_html = """
{% extends "base.html" %}
{% block content %}
<h2>✨ Inspiration #{{ insp.inspiration_id }}</h2>

<div class="detail-card">
    <h3>基本情報</h3>
    <div class="detail-row">
        <div class="detail-label">Inspiration ID</div>
        <div class="detail-value">{{ insp.inspiration_id }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">キャラクター</div>
        <div class="detail-value"><strong>{{ insp.character }}</strong></div>
    </div>
    <div class="detail-row">
        <div class="detail-label">Status</div>
        <div class="detail-value"><span class="badge badge-{{ insp.status }}">{{ insp.status }}</span></div>
    </div>
    <div class="detail-row">
        <div class="detail-label">Confidence</div>
        <div class="detail-value">{{ "%.2f"|format(insp.confidence) }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">Mention Count</div>
        <div class="detail-value">{{ insp.mention_count }}</div>
    </div>
</div>

<div class="detail-card">
    <h3>Original Hallucination (最初のハルシネーション)</h3>
    <pre>{{ insp.original_hallucination }}</pre>
</div>

<div class="detail-card">
    <h3>Inspired Value (抽出された価値観)</h3>
    <pre>{{ insp.inspired_value }}</pre>
</div>

<div class="detail-card">
    <h3>Timeline</h3>
    <div class="detail-row">
        <div class="detail-label">Origin Event ID</div>
        <div class="detail-value">
            <a href="/event/{{ insp.event_id_origin }}" class="btn">Event #{{ insp.event_id_origin }}</a>
        </div>
    </div>
    <div class="detail-row">
        <div class="detail-label">Created At</div>
        <div class="detail-value">{{ insp.created_at }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">Last Mentioned At</div>
        <div class="detail-value">{{ insp.last_mentioned_at }}</div>
    </div>
    {% if insp.realized_at %}
    <div class="detail-row">
        <div class="detail-label">Realized At</div>
        <div class="detail-value">{{ insp.realized_at }}</div>
    </div>
    <div class="detail-row">
        <div class="detail-label">Realization Event ID</div>
        <div class="detail-value">
            <a href="/event/{{ insp.event_id_realization }}" class="btn">Event #{{ insp.event_id_realization }}</a>
        </div>
    </div>
    {% endif %}
</div>

<a href="/inspirations" class="btn">← Inspiration一覧に戻る</a>
{% endblock %}
"""

    return render_template_string(BASE_TEMPLATE + detail_html, page='inspirations', insp=insp)


if __name__ == '__main__':
    print("="*70)
    print("Copy Robot Database Viewer - Starting...")
    print("="*70)
    print()
    print(f"Database: {COPY_ROBOT_DB}")
    print()
    print("Access the viewer at:")
    print("  http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*70)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)
