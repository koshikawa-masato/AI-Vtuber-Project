"""
Seed Knowledge Base with Hololive Information
==============================================

Populate static knowledge about VTubers, units, nicknames, etc.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH


def seed_units():
    """Add VTuber units (ド珍組, みっころね, etc.)"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Units data
    units = [
        {
            'unit_name': 'ド珍組',
            'unit_name_kana': 'どちんぐみ',
            'description': 'さくらみこ、大神ミオ、大空スバル、白上フブキの4人組ユニット',
            'official': 0,
            'notes': 'ホラゲーコラボなどで活動'
        },
        {
            'unit_name': 'みっころね',
            'unit_name_kana': 'みっころね',
            'description': 'さくらみこと戌神ころねのコンビ',
            'official': 0,
            'notes': 'ゲームコラボで人気'
        },
        {
            'unit_name': 'UMISEA',
            'unit_name_kana': 'うみしー',
            'description': '海モチーフのVTuberユニット',
            'official': 1,
            'notes': '宝鐘マリン、白上フブキ、一伊那尓栖、がうる・ぐら'
        },
        {
            'unit_name': 'ホロライブゲーマーズ',
            'unit_name_kana': 'ほろらいぶげーまーず',
            'description': 'ゲーム特化ユニット',
            'official': 1,
            'notes': '白上フブキ、大神ミオ、猫又おかゆ、戌神ころね'
        },
    ]

    for unit in units:
        cursor.execute("""
        INSERT OR IGNORE INTO vtuber_units (unit_name, unit_name_kana, description, official, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (unit['unit_name'], unit['unit_name_kana'], unit['description'],
              unit['official'], unit['notes']))

    conn.commit()
    print(f"[SUCCESS] Added {len(units)} units")

    # Add unit members
    unit_members = [
        # ド珍組
        ('ド珍組', 'さくらみこ'),
        ('ド珍組', '大神ミオ'),
        ('ド珍組', '大空スバル'),
        ('ド珍組', '白上フブキ'),

        # みっころね
        ('みっころね', 'さくらみこ'),
        ('みっころね', '戌神ころね'),

        # UMISEA
        ('UMISEA', '宝鐘マリン'),
        ('UMISEA', '白上フブキ'),
        ('UMISEA', '一伊那尓栖'),
        ('UMISEA', 'がうる・ぐら'),

        # ゲーマーズ
        ('ホロライブゲーマーズ', '白上フブキ'),
        ('ホロライブゲーマーズ', '大神ミオ'),
        ('ホロライブゲーマーズ', '猫又おかゆ'),
        ('ホロライブゲーマーズ', '戌神ころね'),
    ]

    for unit_name, vtuber_name in unit_members:
        cursor.execute("""
        INSERT OR IGNORE INTO vtuber_unit_members (unit_id, vtuber_id)
        SELECT u.unit_id, v.vtuber_id
        FROM vtuber_units u, vtubers v
        WHERE u.unit_name = ? AND v.name = ?
        """, (unit_name, vtuber_name))

    conn.commit()
    print(f"[SUCCESS] Added {len(unit_members)} unit memberships")

    conn.close()


def seed_nicknames():
    """Add common VTuber nicknames"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nicknames = [
        # さくらみこ
        ('さくらみこ', 'みこち', 'ファン呼び', 1),
        ('さくらみこ', 'エリート', 'キャラ特性', 0),
        ('さくらみこ', 'エリート巫女', 'キャッチフレーズ', 0),

        # 戌神ころね
        ('戌神ころね', 'ころねさん', 'ファン呼び', 1),
        ('戌神ころね', 'ころね', 'ファン呼び', 1),
        ('戌神ころね', '犬', 'モチーフ', 0),

        # 宝鐘マリン
        ('宝鐘マリン', 'マリン船長', 'ファン呼び', 1),
        ('宝鐘マリン', '船長', 'ファン呼び', 1),
        ('宝鐘マリン', 'マリン', 'ファン呼び', 1),

        # 白上フブキ
        ('白上フブキ', 'フブキ', 'ファン呼び', 1),
        ('白上フブキ', 'フブちゃん', 'メンバー呼び', 0),
        ('白上フブキ', 'フブさん', 'メンバー呼び', 0),

        # 大神ミオ
        ('大神ミオ', 'ミオ', 'ファン呼び', 1),
        ('大神ミオ', 'ミオしゃ', 'メンバー呼び', 0),
        ('大神ミオ', 'ミオちゃん', 'メンバー呼び', 0),

        # 大空スバル
        ('大空スバル', 'スバル', 'ファン呼び', 1),
        ('大空スバル', 'スバちゃん', 'メンバー呼び', 0),
    ]

    for vtuber_name, nickname, nickname_type, is_primary in nicknames:
        cursor.execute("""
        INSERT OR IGNORE INTO vtuber_nicknames (vtuber_id, nickname, nickname_type, is_primary)
        SELECT vtuber_id, ?, ?, ?
        FROM vtubers
        WHERE name = ?
        """, (nickname, nickname_type, is_primary, vtuber_name))

    conn.commit()
    print(f"[SUCCESS] Added {len(nicknames)} nicknames")

    conn.close()


def seed_trivia():
    """Add VTuber trivia (catchphrases, characteristics)"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    trivia_items = [
        # さくらみこ
        ('さくらみこ', '口癖', '「にぇ」「にぇにぇ」という語尾', 'wiki', 1),
        ('さくらみこ', 'キャッチフレーズ', 'エリート巫女', 'wiki', 1),
        ('さくらみこ', '特徴', 'ポンコツムーブで愛されるキャラ', 'ファン認識', 1),

        # 戌神ころね
        ('戌神ころね', '口癖', '「なーほーね」「ゆびゆび」', 'wiki', 1),
        ('戌神ころね', '特徴', 'レトロゲーム好き、耐久配信', 'wiki', 1),
        ('戌神ころね', 'ミーム', 'DOOG（海外ファン）', 'ファン認識', 1),

        # 宝鐘マリン
        ('宝鐘マリン', 'キャッチフレーズ', '宝鐘の17歳（自称）', 'wiki', 1),
        ('宝鐘マリン', '特徴', '歌唱力が高い、ソロライブ経験多数', 'wiki', 1),

        # 白上フブキ
        ('白上フブキ', '特徴', 'ホロライブの顔、多方面で活躍', 'wiki', 1),
        ('白上フブキ', 'ミーム', 'scatman（歌ってみた）', 'ファン認識', 1),

        # 大神ミオ
        ('大神ミオ', 'キャッチフレーズ', 'ホロライブのママ', 'ファン認識', 1),

        # 大空スバル
        ('大空スバル', '特徴', '元気なトーク、体育会系', 'wiki', 1),
        ('大空スバル', 'ミーム', '野球選手（ド珍組での役割）', 'コラボ', 0),
    ]

    for vtuber_name, category, content, source, verified in trivia_items:
        cursor.execute("""
        INSERT OR IGNORE INTO vtuber_trivia (vtuber_id, category, content, source, verified)
        SELECT vtuber_id, ?, ?, ?, ?
        FROM vtubers
        WHERE name = ?
        """, (category, content, source, verified, vtuber_name))

    conn.commit()
    print(f"[SUCCESS] Added {len(trivia_items)} trivia items")

    conn.close()


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Seeding Knowledge Base")
    print("=" * 60)

    seed_units()
    seed_nicknames()
    seed_trivia()

    print("\n" + "=" * 60)
    print("Knowledge Base Seeded Successfully")
    print("=" * 60)


if __name__ == '__main__':
    main()
