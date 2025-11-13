#!/usr/bin/env python3
"""
copy_robot_memory.db 作成スクリプト

VPS用のコピーロボット記憶データベースを作成します。
Phase D完全実装前の簡易版として、最低限のテストデータを投入します。
"""

import sqlite3
import os
from datetime import datetime

# プロジェクトルート
PROJECT_ROOT = "/home/koshikawa/AI-Vtuber-Project"
DB_PATH = os.path.join(PROJECT_ROOT, "copy_robot_memory.db")

def create_database():
    """データベースとテーブルを作成"""

    # 既存のファイルがあれば削除
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ 既存の{DB_PATH}を削除")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ========================================
    # テーブル作成
    # ========================================

    # 牡丹の記憶テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS botan_memories (
            memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            absolute_day INTEGER NOT NULL,
            memory_date TEXT NOT NULL,

            -- 牡丹の主観的記憶
            botan_emotion TEXT,
            botan_action TEXT,
            botan_thought TEXT,
            diary_entry TEXT,

            -- 姉妹の観察
            kasho_observed_behavior TEXT,
            yuri_observed_behavior TEXT,

            -- 姉妹への推測
            kasho_inferred_feeling TEXT,
            yuri_inferred_feeling TEXT,

            memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),
            memory_type TEXT DEFAULT 'direct',
            confidence_level INTEGER DEFAULT 8,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Kashoの記憶テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kasho_memories (
            memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            absolute_day INTEGER NOT NULL,
            memory_date TEXT NOT NULL,

            kasho_emotion TEXT,
            kasho_action TEXT,
            kasho_thought TEXT,
            diary_entry TEXT,

            botan_observed_behavior TEXT,
            yuri_observed_behavior TEXT,

            botan_inferred_feeling TEXT,
            yuri_inferred_feeling TEXT,

            memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),
            memory_type TEXT DEFAULT 'direct',
            confidence_level INTEGER DEFAULT 8,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ユリの記憶テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS yuri_memories (
            memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            absolute_day INTEGER NOT NULL,
            memory_date TEXT NOT NULL,

            yuri_emotion TEXT,
            yuri_action TEXT,
            yuri_thought TEXT,
            diary_entry TEXT,

            kasho_observed_behavior TEXT,
            botan_observed_behavior TEXT,

            kasho_inferred_feeling TEXT,
            botan_inferred_feeling TEXT,

            memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),
            memory_type TEXT DEFAULT 'direct',
            confidence_level INTEGER DEFAULT 8,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 共有イベントテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sister_shared_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            absolute_day INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            event_title TEXT NOT NULL,
            event_description TEXT,
            event_type TEXT,
            location TEXT,

            kasho_present BOOLEAN DEFAULT 1,
            botan_present BOOLEAN DEFAULT 1,
            yuri_present BOOLEAN DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    print("✅ テーブル作成完了")

    return conn, cursor


def insert_test_data(conn, cursor):
    """テストデータを投入"""

    print("\n📝 テストデータ投入中...")

    # ========================================
    # 共有イベント
    # ========================================

    events = [
        (1, "2020-04-01", "中学入学", "牡丹が中学に入学。新しい環境に少し緊張。", "school", "日本"),
        (100, "2022-08-15", "LA移住", "家族でLAに移住。新しい生活が始まる。", "life_event", "LA"),
        (500, "2024-06-10", "日本帰国", "LAから日本に帰国。懐かしい場所に戻る。", "life_event", "日本"),
    ]

    cursor.executemany("""
        INSERT INTO sister_shared_events
        (absolute_day, event_date, event_title, event_description, event_type, location,
         kasho_present, botan_present, yuri_present)
        VALUES (?, ?, ?, ?, ?, ?, 1, 1, 1)
    """, events)

    print("  ✅ 共有イベント: 3件")

    # ========================================
    # 牡丹の記憶
    # ========================================

    botan_memories = [
        (
            1, 1, "2020-04-01",
            "ドキドキ", "新しい制服を着て登校", "新しい友達できるかな...",
            "中学入学初日。めっちゃ緊張したけど、新しい友達ができて嬉しかった！",
            "Kashoお姉ちゃんが励ましてくれた", "ユリは少し寂しそうだった",
            "お姉ちゃんも心配してたのかも", "ユリは私がいないのが寂しいのかな",
            8, "direct", 9
        ),
        (
            2, 100, "2022-08-15",
            "不安と期待", "LAの新しい家に到着", "英語...大丈夫かな",
            "LAに着いた。めっちゃ不安だったけど、新しい生活が楽しみでもある。",
            "Kashoは冷静に準備してた", "ユリは興奮してた",
            "お姉ちゃんは私たちのために頑張ってる", "ユリは新しい環境を楽しんでる",
            10, "direct", 10
        ),
        (
            3, 500, "2024-06-10",
            "懐かしさ", "日本の空港に降り立つ", "やっぱり日本が好きだな",
            "日本に帰ってきた！LAも良かったけど、やっぱり日本が落ち着く。",
            "Kashoも嬉しそうだった", "ユリは日本の景色を楽しんでた",
            "お姉ちゃんも日本が恋しかったんだね", "ユリは日本の文化を再発見してる",
            9, "direct", 9
        ),
    ]

    cursor.executemany("""
        INSERT INTO botan_memories
        (event_id, absolute_day, memory_date,
         botan_emotion, botan_action, botan_thought, diary_entry,
         kasho_observed_behavior, yuri_observed_behavior,
         kasho_inferred_feeling, yuri_inferred_feeling,
         memory_importance, memory_type, confidence_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, botan_memories)

    print("  ✅ 牡丹の記憶: 3件")

    # ========================================
    # Kashoの記憶
    # ========================================

    kasho_memories = [
        (
            1, 1, "2020-04-01",
            "心配", "牡丹を見送る", "妹が無事に学校に馴染めるといいな",
            "牡丹が中学に入学。少し心配だけど、きっと大丈夫。",
            "牡丹は緊張してた", "ユリは寂しそうだった",
            "牡丹は不安だったのかも", "ユリは牡丹がいないのが寂しいんだね",
            7, "direct", 8
        ),
    ]

    cursor.executemany("""
        INSERT INTO kasho_memories
        (event_id, absolute_day, memory_date,
         kasho_emotion, kasho_action, kasho_thought, diary_entry,
         botan_observed_behavior, yuri_observed_behavior,
         botan_inferred_feeling, yuri_inferred_feeling,
         memory_importance, memory_type, confidence_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, kasho_memories)

    print("  ✅ Kashoの記憶: 1件")

    # ========================================
    # ユリの記憶
    # ========================================

    yuri_memories = [
        (
            1, 1, "2020-04-01",
            "寂しい", "牡丹を見送る", "お姉ちゃんがいない学校...寂しいな",
            "牡丹お姉ちゃんが中学に入学。少し寂しい。",
            "Kashoお姉ちゃんは優しく見守ってた", "牡丹お姉ちゃんは緊張してた",
            "Kashoお姉ちゃんは牡丹のこと心配してる", "牡丹お姉ちゃんは不安そうだった",
            6, "direct", 8
        ),
    ]

    cursor.executemany("""
        INSERT INTO yuri_memories
        (event_id, absolute_day, memory_date,
         yuri_emotion, yuri_action, yuri_thought, diary_entry,
         kasho_observed_behavior, botan_observed_behavior,
         kasho_inferred_feeling, botan_inferred_feeling,
         memory_importance, memory_type, confidence_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, yuri_memories)

    print("  ✅ ユリの記憶: 1件")

    conn.commit()


def verify_database(conn, cursor):
    """データベースの内容を確認"""

    print("\n🔍 データベース検証中...")

    # 各テーブルのレコード数を確認
    tables = [
        "sister_shared_events",
        "botan_memories",
        "kasho_memories",
        "yuri_memories"
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  ✅ {table}: {count}件")

    # 牡丹の記憶サンプル表示
    print("\n📖 牡丹の記憶サンプル:")
    cursor.execute("""
        SELECT memory_date, diary_entry
        FROM botan_memories
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"  日付: {row[0]}")
        print(f"  日記: {row[1]}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("🤖 copy_robot_memory.db 作成スクリプト")
    print("=" * 60)

    # データベース作成
    conn, cursor = create_database()

    # テストデータ投入
    insert_test_data(conn, cursor)

    # 検証
    verify_database(conn, cursor)

    # クローズ
    conn.close()

    # ファイルサイズ確認
    file_size = os.path.getsize(DB_PATH)
    print(f"\n✅ copy_robot_memory.db 作成完了: {file_size:,} bytes")
    print(f"   保存先: {DB_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
