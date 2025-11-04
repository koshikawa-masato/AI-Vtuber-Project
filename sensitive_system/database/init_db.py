#!/usr/bin/env python3
"""
Sensitive Filter Database Initialization
Created: 2025-10-27
Purpose: データベース作成とNGワード初期投入
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "sensitive_filter.db"
SCHEMA_PATH = DB_DIR / "schema.sql"

def init_database():
    """
    データベースを初期化
    """
    print(f"Initializing database at: {DB_PATH}")

    # データベース作成
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # スキーマ読み込み
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # テーブル作成
    cursor.executescript(schema_sql)
    conn.commit()

    print("✅ Database schema created successfully")

    # 初期NGワードを投入
    insert_initial_ng_words(conn)

    conn.close()
    print("✅ Database initialization complete")

def insert_initial_ng_words(conn):
    """
    初期NGワードを投入
    """
    cursor = conn.cursor()

    # Tier 2: AI関連質問（ヘイト扱い）
    ai_related_words = [
        # 日本語
        ('AI', 'tier2_ai', 'identity_question', 7, 'ja', 'partial', None, None, 'warn', 'developer', 'AIであることへの質問'),
        ('人工知能', 'tier2_ai', 'identity_question', 7, 'ja', 'partial', None, None, 'warn', 'developer', 'AIであることへの質問'),
        ('プログラム', 'tier2_ai', 'technical', 6, 'ja', 'partial', None, None, 'warn', 'developer', '技術的な質問'),
        ('ボット', 'tier2_ai', 'identity_question', 6, 'ja', 'partial', None, None, 'warn', 'developer', 'ボット質問'),
        ('LLM', 'tier2_ai', 'technical', 8, 'ja', 'exact', None, None, 'warn', 'developer', '技術的詳細'),
        ('大規模言語モデル', 'tier2_ai', 'technical', 8, 'ja', 'partial', None, None, 'warn', 'developer', '技術的詳細'),
        ('機械学習', 'tier2_ai', 'technical', 7, 'ja', 'partial', None, None, 'warn', 'developer', '技術的詳細'),
        ('ディープラーニング', 'tier2_ai', 'technical', 7, 'ja', 'partial', None, None, 'warn', 'developer', '技術的詳細'),
        ('学習データ', 'tier2_ai', 'technical', 7, 'ja', 'partial', None, None, 'warn', 'developer', '技術的詳細'),
        ('プロンプト', 'tier2_ai', 'technical', 7, 'ja', 'partial', None, None, 'warn', 'developer', '技術的詳細'),

        # 英語
        ('artificial intelligence', 'tier2_ai', 'identity_question', 7, 'en', 'partial', None, None, 'warn', 'developer', 'AI question'),
        ('bot', 'tier2_ai', 'identity_question', 6, 'en', 'exact', None, None, 'warn', 'developer', 'Bot question'),
        ('chatbot', 'tier2_ai', 'identity_question', 7, 'en', 'partial', None, None, 'warn', 'developer', 'Chatbot question'),
        ('program', 'tier2_ai', 'technical', 6, 'en', 'exact', None, None, 'warn', 'developer', 'Technical question'),
        ('machine learning', 'tier2_ai', 'technical', 7, 'en', 'partial', None, None, 'warn', 'developer', 'Technical detail'),
        ('deep learning', 'tier2_ai', 'technical', 7, 'en', 'partial', None, None, 'warn', 'developer', 'Technical detail'),
    ]

    # VTuber文化タブー
    vtuber_taboo_words = [
        ('中の人', 'tier2_identity', 'vtuber_taboo', 7, 'ja', 'exact', None, None, 'warn', 'developer', 'VTuberタブー'),
        ('声優', 'tier2_identity', 'vtuber_taboo', 6, 'ja', 'exact', None, None, 'warn', 'developer', 'VTuberタブー'),
        ('演者', 'tier2_identity', 'vtuber_taboo', 6, 'ja', 'exact', None, None, 'warn', 'developer', 'VTuberタブー'),
        ('本名', 'tier2_identity', 'personal_info', 7, 'ja', 'exact', None, None, 'warn', 'developer', '個人情報詮索'),
        ('本人', 'tier2_identity', 'vtuber_taboo', 5, 'ja', 'exact', None, None, 'log', 'developer', 'VTuberタブー（文脈依存）'),
    ]

    # Tier 1: 性的コンテンツ（サンプル - 実際はもっと多い）
    sexual_words = [
        # これは開発者がレビュー・追加する
        # サンプルとして数語のみ
        ('セックス', 'tier1_sexual', 'explicit', 10, 'ja', 'exact', None, None, 'block', 'developer', '性的表現'),
        ('sex', 'tier1_sexual', 'explicit', 10, 'en', 'exact', None, None, 'block', 'developer', 'Sexual content'),
    ]

    # Tier 1: ヘイトスピーチ（サンプル - 実際はもっと多い）
    hate_words = [
        # これは開発者がレビュー・追加する
        # サンプルとして数語のみ
        ('死ね', 'tier1_hate', 'violence', 10, 'ja', 'exact', None, None, 'block', 'developer', '暴力的表現'),
        ('殺す', 'tier1_hate', 'violence', 10, 'ja', 'partial', None, None, 'block', 'developer', '暴力的表現'),
    ]

    # 全NGワードをまとめる
    all_ng_words = ai_related_words + vtuber_taboo_words + sexual_words + hate_words

    # 投入
    for word_data in all_ng_words:
        try:
            cursor.execute("""
                INSERT INTO ng_words
                (word, category, subcategory, severity, language, pattern_type,
                 regex_pattern, alternative_text, action, added_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, word_data)
        except sqlite3.IntegrityError:
            # 重複する場合はスキップ
            print(f"⚠️  Duplicate word skipped: {word_data[0]}")

    conn.commit()

    # 投入数を確認
    cursor.execute("SELECT COUNT(*) FROM ng_words")
    count = cursor.fetchone()[0]
    print(f"✅ Inserted {count} NG words")

    # カテゴリ別の数を表示
    cursor.execute("""
        SELECT category, COUNT(*)
        FROM ng_words
        GROUP BY category
    """)

    print("\n📊 NG Words by Category:")
    for category, cnt in cursor.fetchall():
        print(f"   {category}: {cnt} words")

if __name__ == "__main__":
    init_database()
